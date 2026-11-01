from collections import OrderedDict
from dataclasses import dataclass
from time import monotonic

import httpx


@dataclass
class ProviderError(Exception):
    status: int
    message: str


class MockProvider:
    """Offline fixtures; deliberately never presented as live weather."""

    async def weather(self, city: str, location_id: int | None = None) -> dict:
        cities = {
            "atlanta": ("Atlanta, GA, US", 22, "Partly cloudy"),
            "new york": ("New York, NY, US", 16, "Cloudy"),
            "london": ("London, GB", 12, "Light rain"),
            "lagos": ("Lagos, NG", 29, "Sunny"),
        }
        key = city.casefold()
        if key == "springfield":
            raise ProviderError(409, "Ambiguous city. Choose Atlanta, New York, London, or Lagos in demo mode.")
        if key not in cities:
            raise ProviderError(404, "City not in demo dataset. Try Atlanta, New York, London, or Lagos.")
        name, temperature, condition = cities[key]
        return {
            "city": name, "temperature": temperature, "unit": "C",
            "condition": condition, "observed_at": "2026-10-31T12:00:00Z",
            "provider": "deterministic-demo", "demo": True,
        }


class OpenMeteoProvider:
    """Bounded, process-local five-minute cache; no credentials required."""

    def __init__(self, transport=None, clock=monotonic):
        self.transport = transport
        self.clock = clock
        self.cache = OrderedDict()

    async def weather(self, city: str, location_id: int | None = None) -> dict:
        key = f"id:{location_id}" if location_id else city.strip().casefold()
        cached = self.cache.get(key)
        if cached and self.clock() < cached[0]:
            self.cache.move_to_end(key)
            return dict(cached[1])
        try:
            async with httpx.AsyncClient(timeout=2.5, transport=self.transport) as client:
                if location_id:
                    location = await self._get(client, 'https://geocoding-api.open-meteo.com/v1/get', {'id': location_id})
                    if not location.get('name'):
                        raise ProviderError(404, 'Location not found.')
                else:
                    locations = await self._get(client, 'https://geocoding-api.open-meteo.com/v1/search',
                                                {'name': city, 'count': 10, 'language': 'en', 'format': 'json'})
                    matches = locations.get('results', [])
                    city_name = city.split(',', 1)[0].strip().casefold()
                    exact = [place for place in matches if place.get('name', '').casefold() == city_name]
                    if exact:
                        matches = exact
                    if not matches:
                        raise ProviderError(404, 'City not found. Check the spelling or add a region.')
                    if len(matches) > 1:
                        raise ProviderError(409, 'Multiple locations found. Add a region or country, such as Atlanta, Georgia.')
                    location = matches[0]
                data = await self._get(client, 'https://api.open-meteo.com/v1/forecast', {
                    'latitude': location['latitude'], 'longitude': location['longitude'],
                    'current': 'temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m',
                    'timezone': 'GMT', 'temperature_unit': 'celsius', 'wind_speed_unit': 'kmh',
                })
                current = data['current']
                temperature = current['temperature_2m']
                if not isinstance(temperature, (int, float)):
                    raise TypeError('Missing temperature')
                result = {
                    'city': ', '.join(str(location[k]) for k in ('name', 'admin1', 'country_code') if location.get(k)),
                    'temperature': temperature, 'unit': 'C',
                    'condition': condition_name(current['weather_code']),
                    'observed_at': current['time'] + 'Z', 'provider': 'open-meteo', 'demo': False,
                    'humidity': current['relative_humidity_2m'], 'wind_speed': current['wind_speed_10m'],
                    'wind_unit': 'km/h', 'data_kind': 'model-based current conditions',
                }
        except httpx.TimeoutException as exc:
            raise TimeoutError() from exc
        except (httpx.HTTPError, KeyError, ValueError, TypeError) as exc:
            raise ProviderError(503, 'Weather provider unavailable.') from exc
        self.cache[key] = (self.clock() + 300, result)
        self.cache.move_to_end(key)
        while len(self.cache) > 128:
            self.cache.popitem(last=False)
        return dict(result)

    async def search(self, query):
        try:
            async with httpx.AsyncClient(timeout=2.5, transport=self.transport) as client:
                data = await self._get(client, 'https://geocoding-api.open-meteo.com/v1/search',
                                       {'name': query, 'count': 20, 'language': 'en'})
            return [{'id': place['id'], 'label': ', '.join(str(place[k]) for k in
                     ('name', 'admin1', 'country') if place.get(k))}
                    for place in data.get('results', [])
                    if place.get('feature_code', '').startswith('PPL')][:10]
        except httpx.TimeoutException as exc:
            raise TimeoutError() from exc
        except (httpx.HTTPError, KeyError, ValueError, TypeError) as exc:
            raise ProviderError(503, 'Location search unavailable.') from exc

    @staticmethod
    async def _get(client, url, params):
        response = await client.get(url, params=params)
        if response.status_code == 429:
            raise ProviderError(429, 'Weather provider rate limit reached.')
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise TypeError('Invalid provider response')
        return data


def condition_name(code):
    names = {0: 'Clear sky', 1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
             45: 'Fog', 48: 'Depositing rime fog', 51: 'Light drizzle', 53: 'Moderate drizzle',
             55: 'Dense drizzle', 56: 'Light freezing drizzle', 57: 'Dense freezing drizzle',
             61: 'Light rain', 63: 'Moderate rain', 65: 'Heavy rain', 66: 'Light freezing rain',
             67: 'Heavy freezing rain', 71: 'Light snow', 73: 'Moderate snow', 75: 'Heavy snow',
             77: 'Snow grains', 80: 'Light rain showers', 81: 'Moderate rain showers',
             82: 'Violent rain showers', 85: 'Light snow showers', 86: 'Heavy snow showers',
             95: 'Thunderstorm', 96: 'Thunderstorm with slight hail', 99: 'Thunderstorm with heavy hail'}
    return names.get(code, 'Unknown conditions')
