import httpx
from fastapi.testclient import TestClient

from app.main import create_app
from app.provider import OpenMeteoProvider

CURRENT = {'temperature_2m': 25, 'weather_code': 0, 'time': '2026-10-31T12:00',
           'relative_humidity_2m': 50, 'wind_speed_10m': 10}


def test_suggestions_filter_airports_and_use_selected_id():
    city = {'id': 2337639, 'name': 'Ilorin', 'admin1': 'Kwara State', 'country': 'Nigeria',
            'country_code': 'NG', 'latitude': 8.49664, 'longitude': 4.54214, 'feature_code': 'PPLA'}
    seen = []

    def handler(request):
        seen.append(request)
        if request.url.path.endswith('/search'):
            return httpx.Response(200, json={'results': [city, {**city, 'id': 2, 'feature_code': 'AIRP'}]})
        if request.url.path.endswith('/get'):
            assert request.url.params['id'] == '2337639'
            return httpx.Response(200, json=city)
        assert request.url.params['latitude'] == '8.49664'
        return httpx.Response(200, json={'current': CURRENT})

    with TestClient(create_app(provider=OpenMeteoProvider(httpx.MockTransport(handler)), mode='openmeteo')) as client:
        results = client.get('/api/locations?q=Ilorin').json()['results']
        assert results == [{'id': 2337639, 'label': 'Ilorin, Kwara State, Nigeria'}]
        response = client.get('/api/weather?location_id=2337639')
        assert response.status_code == 200
        assert response.json()['city'] == 'Ilorin, Kwara State, NG'
        assert len(seen) == 3
        assert client.get('/api/weather?location_id=2337639').status_code == 200
        assert len(seen) == 3


def test_search_validation_and_mock_selection():
    with TestClient(create_app(mode='mock')) as client:
        assert client.get('/api/locations?q=a').status_code == 422
        assert client.get('/api/locations?q=Atlant').json()['results'] == [{'id': None, 'label': 'Atlanta'}]
        assert client.get('/api/locations?q=unknown').json()['results'] == []
        assert client.get('/api/weather?location_id=-1').status_code == 422
        assert client.get('/api/weather?location_id=123').status_code == 422


def test_search_rate_limit_is_safe():
    provider = OpenMeteoProvider(httpx.MockTransport(lambda request: httpx.Response(429, text='private')))
    with TestClient(create_app(provider=provider, mode='openmeteo')) as client:
        response = client.get('/api/locations?q=Ilorin')
        assert response.status_code == 429
        assert 'private' not in response.text
