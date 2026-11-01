import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.provider import OpenMeteoProvider

LOCATION = {'name': 'Atlanta', 'admin1': 'Georgia', 'country_code': 'US', 'latitude': 33.75, 'longitude': -84.39}
CURRENT = {'temperature_2m': 22.5, 'weather_code': 2, 'time': '2026-10-31T12:00',
           'relative_humidity_2m': 60, 'wind_speed_10m': 12}


def test_live_normalization_cache_and_expiry():
    calls, now = [], [0]

    def handler(request):
        calls.append(request)
        if request.url.host.startswith('geocoding'):
            return httpx.Response(200, json={'results': [LOCATION, {**LOCATION, 'name': 'Atlanta Junction'}]})
        assert request.url.params['timezone'] == 'GMT'
        return httpx.Response(200, json={'current': CURRENT})

    provider = OpenMeteoProvider(httpx.MockTransport(handler), clock=lambda: now[0])
    with TestClient(create_app(provider=provider, mode='openmeteo')) as client:
        first = client.get('/api/weather?city=Atlanta').json()
        assert first['temperature'] == 22.5
        assert first['condition'] == 'Partly cloudy'
        assert first['observed_at'].endswith('Z')
        assert first['demo'] is False
        assert client.get('/api/weather?city=ATLANTA').json() == first
        assert len(calls) == 2
        now[0] = 301
        assert client.get('/api/weather?city=Atlanta').status_code == 200
        assert len(calls) == 4


@pytest.mark.parametrize('scenario,status', [('missing',404), ('ambiguous',409), ('rate',429),
                                          ('server',503), ('malformed',503), ('timeout',504)])
def test_live_failures(scenario, status):
    def handler(request):
        if scenario == 'timeout':
            raise httpx.ReadTimeout('private upstream details', request=request)
        if scenario == 'rate':
            return httpx.Response(429)
        if scenario == 'server':
            return httpx.Response(500, text='private upstream details')
        if scenario == 'malformed':
            return httpx.Response(200, text='not json')
        return httpx.Response(200, json={'results': [] if scenario == 'missing' else [LOCATION, LOCATION]})

    provider = OpenMeteoProvider(httpx.MockTransport(handler))
    with TestClient(create_app(provider=provider, mode='openmeteo')) as client:
        response = client.get('/api/weather?city=Atlanta')
        assert response.status_code == status
        assert 'private upstream details' not in response.text
        assert not provider.cache
        assert client.get('/ready').status_code == 200


def test_cache_is_bounded():
    def handler(request):
        data = {'results': [LOCATION]} if request.url.host.startswith('geocoding') else {'current': CURRENT}
        return httpx.Response(200, json=data)

    provider = OpenMeteoProvider(httpx.MockTransport(handler))
    with TestClient(create_app(provider=provider, mode='openmeteo')) as client:
        for index in range(130):
            assert client.get('/api/weather', params={'city': f'city{index}'}).status_code == 200
    assert len(provider.cache) == 128
