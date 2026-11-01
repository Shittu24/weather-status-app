"""Run against a real process/container; uses only the standard library."""
import json
import sys
from urllib.request import urlopen

base = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8000'
with urlopen(base + '/version', timeout=5) as response:
    city = 'Atlanta' if json.load(response)['mode'] == 'mock' else 'Atlanta%2C%20Georgia'
for path, expected in [('/health', 'status'), ('/ready', 'status'),
                       ('/version', 'commit'), ('/api/weather?city=' + city, 'temperature')]:
    with urlopen(base + path, timeout=8) as response:
        assert response.status == 200
        assert expected in json.load(response)
    print('PASS', path)
