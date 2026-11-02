import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.provider import ProviderError


@pytest.fixture
def client():
    with TestClient(create_app(mode="mock")) as client:
        yield client


def test_weather_contract(client):
    response = client.get('/api/weather', params={'city': '  ATLANTA  '})
    assert response.status_code == 200
    assert response.json() == {'city': 'Atlanta, GA, US', 'temperature': 22, 'unit': 'C',
                               'condition': 'Partly cloudy', 'observed_at': '2026-10-31T12:00:00Z',
                               'provider': 'deterministic-demo', 'demo': True}
    assert response.headers['x-request-id']


@pytest.mark.parametrize('city,status', [('Atlantis',404), ('Springfield',409), (' ',422), ('x'*81,422), ('\n',422)])
def test_bad_city(client, city, status):
    assert client.get('/api/weather', params={'city':city}).status_code == status


@pytest.mark.parametrize('error,status', [(TimeoutError(),504), (ProviderError(429,'secret'),429),
                                        (ProviderError(503,'secret'),503), (RuntimeError('secret'),503)])
def test_provider_errors_are_safe(error, status):
    class BrokenProvider:
        async def weather(self, city):
            raise error
    with TestClient(create_app(provider=BrokenProvider(), mode="mock")) as client:
        response = client.get('/api/weather?city=Atlanta')
        assert response.status_code == status
        assert 'secret' not in response.text
        assert client.get('/health').status_code == 200
        assert client.get('/ready').status_code == 200


def test_invalid_configuration():
    with pytest.raises(ValueError, match='WEATHER_MODE'):
        create_app(mode='live')


def test_page_and_release(client):
    assert 'Offline demo' in client.get('/').text
    assert client.get('/version').json()['version'] == '0.1.0'


def test_metrics_have_bounded_labels(client):
    client.get('/api/weather?city=PRIVATE_CITY')
    client.get('/arbitrary-private-path')
    metrics = client.get('/metrics').text
    assert 'weather_http_requests_total' in metrics
    assert 'PRIVATE_CITY' not in metrics
    assert 'arbitrary-private-path' not in metrics


def test_logs_exclude_query(client, caplog):
    import logging
    with caplog.at_level(logging.INFO, logger='weather.requests'):
        client.get('/api/weather?city=PRIVATE_CITY')
    assert 'PRIVATE_CITY' not in caplog.text
    assert 'duration_ms' in caplog.text


def test_release_commit_matches_build_metadata(monkeypatch):
    """Expose build metadata so operators can verify deployments and rollbacks."""
    monkeypatch.setenv("APP_COMMIT", "portfolio-release-demo")
    with TestClient(create_app(mode="mock")) as client:
        assert client.get('/version').json()['commit'] == 'portfolio-release-demo'
