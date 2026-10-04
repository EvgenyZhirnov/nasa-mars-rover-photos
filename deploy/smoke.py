"""Check web readiness without depending on live NASA services."""
import json
import sys
import time
from urllib.request import urlopen


def check(base, revision):
    for attempt in range(40):
        try:
            with urlopen(base + '/healthz', timeout=3) as response:
                health = json.load(response)
            if health.get('status') == 'ok' and health.get('revision') == revision:
                break
        except (OSError, ValueError):
            pass
        time.sleep(2)
    else:
        raise RuntimeError('Expected release did not become ready')
    for path in ['/', '/static/explorer.js', '/static/explorer.css']:
        with urlopen(base + path, timeout=5) as response:
            assert response.status == 200 and response.read(100), path
    with urlopen(base + '/api/media/collections', timeout=5) as response:
        catalog = json.load(response)
    assert len(catalog['collections']) >= 24
    print('Release ready:', revision, flush=True)


if __name__ == '__main__':
    check(sys.argv[1].rstrip('/'), sys.argv[2])
