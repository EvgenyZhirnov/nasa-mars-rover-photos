"""Read-only source adapters and bounded stale-while-revalidate disk cache."""
import hashlib
import json
import logging
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlsplit

import requests
import config

log = logging.getLogger(__name__)
CACHE_DIR = config.DATA_DIR / 'api_cache'
_pool = ThreadPoolExecutor(max_workers=6, thread_name_prefix='nasa-source')
_lock = threading.Lock()
_pending = set()
_retry = {}
MAX_ENTRIES = 128


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)


def plain(value):
    parser = TextParser()
    parser.feed(str(value or ''))
    return ' '.join(' '.join(parser.parts).split())


def safe_url(value):
    if not isinstance(value, str):
        return ''
    parsed = urlsplit(value)
    # NASA's asset manifest still publishes HTTP links; this host supports HTTPS.
    if parsed.scheme == 'http' and parsed.netloc == 'images-assets.nasa.gov':
        return parsed._replace(scheme='https').geturl()
    return value if parsed.scheme == 'https' else ''


def get_json(url, params=None):
    response = requests.get(url, params=params, timeout=(5, 20), headers={'User-Agent': 'NasaRoverExplorer/1.0'})
    response.raise_for_status()
    # EONET sometimes labels valid JSON as application/rss+xml. Validate the
    # payload itself, while rejecting HTML redirect pages as failed requests.
    try:
        data = response.json()
    except ValueError as exc:
        raise ValueError('Источник вернул страницу вместо данных') from exc
    if not isinstance(data, (dict, list)):
        raise ValueError('Неверный формат данных источника')
    return data


def normalize_apod(raw):
    data = raw[0] if isinstance(raw, list) and raw else raw
    if not isinstance(data, dict) or not data.get('date'):
        raise ValueError('Нет записи APOD')
    return {'title': plain(data.get('title')), 'date': data['date'],
            'explanation': plain(data.get('explanation')), 'copyright': plain(data.get('copyright') or data.get('credit')),
            'media_type': data.get('media_type'), 'url': safe_url(data.get('permalink') or data.get('url')),
            'hdurl': safe_url(data.get('hdurl')), 'image_url': safe_url(data.get('hdurl'))}


def apod():
    return normalize_apod(get_json('https://science.nasa.gov/wp-json/wp/v2/apod-basic', {'per_page': 1}))


def media(query, page=1, collection=''):
    from media_catalog import BY_ID
    preset = BY_ID.get(collection)
    params = {'q': preset['query'] if preset else query, 'media_type': 'image', 'page_size': 24, 'page': page}
    if preset:
        params.update(preset.get('params', {}))
    payload = get_json('https://images-api.nasa.gov/search', params)['collection']
    items = []
    for item in payload.get('items', []):
        data = item.get('data', [{}])[0]
        links = item.get('links', [])
        thumb = next((safe_url(x.get('href')) for x in links if x.get('render') == 'image'), '')
        items.append({'id': data.get('nasa_id'), 'title': plain(data.get('title')),
                      'description': plain(data.get('description')), 'date': data.get('date_created'),
                      'image_url': thumb, 'url': 'https://images.nasa.gov/details/' + quote(data.get('nasa_id', ''), safe=''),
                      'credit': plain(data.get('secondary_creator') or data.get('photographer') or data.get('center')),
                      'center': data.get('center'), 'keywords': data.get('keywords', []),
                      'kind': media_kind(data.get('title', ''), data.get('description', ''))})
    total = int(payload.get('metadata', {}).get('total_hits', len(items)))
    return {'items': items, 'total': total, 'page': page, 'pages': max(1, (total + 23) // 24),
            'collection': collection, 'title': preset['title'] if preset else query,
            'note': preset['note'] if preset else 'Результаты поиска в NASA Image Library.'}


def media_kind(title, description):
    title = plain(title).lower()
    text = title + ' ' + plain(description).lower()
    if re.search(r"artist(?:'s|’s)? (?:concept|impression|illustration)|artistic impression|this illustration|this artist", text):
        return 'illustration'
    if re.search(r'\b(diagram|graph|chart|simulation|simulated|spectra|spectrum)\b', title):
        return 'diagram'
    if re.search(r'\b(deployment|assembly|technicians|clean room|cleanroom|launch vehicle|mirror installation)\b', title):
        return 'hardware'
    return 'image'


def asset(nasa_id):
    payload = get_json('https://images-api.nasa.gov/asset/' + quote(nasa_id, safe=''))
    links = [safe_url(x.get('href')) for x in payload.get('collection', {}).get('items', [])]
    images = [u for u in links if u and urlsplit(u).path.lower().endswith(('.jpg', '.jpeg', '.png', '.tif', '.tiff'))]
    images.sort(key=lambda u: (0 if '~orig' in u else 1 if '~large' in u else 2, u))
    return {'original_url': images[0] if images else None, 'id': nasa_id}



def rover(name):
    payload = get_json(f'{config.ROVER_API_BASE}/rovers/{name}/latest_photos')
    photos = payload.get('latest_photos', [])
    # Show different cameras instead of only the first camera's entire batch.
    by_camera = {}
    for photo in photos:
        by_camera.setdefault(photo.get('camera', {}).get('name', '?'), []).append(photo)
    selected = []
    while by_camera and len(selected) < 24:
        for key in list(by_camera):
            selected.append(by_camera[key].pop(0))
            if not by_camera[key]:
                del by_camera[key]
            if len(selected) == 24:
                break
    return {'items': [{'id': p['id'], 'sol': p.get('sol'), 'date': p.get('earth_date'),
                       'camera': p.get('camera', {}).get('name'), 'image_url': safe_url(p.get('img_src')),
                       'title': f"{name.capitalize()} · {p.get('camera', {}).get('name', '')}"} for p in selected],
            'total': len(photos), 'provider': 'Nebulum One · сторонний API, снимки NASA'}


def epic(collection, date=''):
    suffix = f'/date/{date}' if date else ''
    photos = get_json(f'https://epic.gsfc.nasa.gov/api/{collection}{suffix}')
    if not isinstance(photos, list):
        raise ValueError('Неверный ответ EPIC')
    items = []
    for p in sorted(photos, key=lambda p: p['date']):
        day = datetime.fromisoformat(p['date']).strftime('%Y/%m/%d')
        name = quote(p['image'], safe='')
        items.append({'date': p['date'], 'image_url': f'https://epic.gsfc.nasa.gov/archive/{collection}/{day}/jpg/{name}.jpg',
                      'centroid': p.get('centroid_coordinates', {})})
    return {'items': items, 'collection': collection}


def asteroids():
    payload = get_json('https://ssd-api.jpl.nasa.gov/cad.api', {'date-min': 'now', 'date-max': '+30', 'dist-max': '10LD', 'sort': 'date'})
    fields = payload['fields']
    items = []
    for row in payload.get('data', []):
        p = dict(zip(fields, row))
        items.append({'name': p['des'], 'date': p['cd'], 'distance_km': round(float(p['dist']) * 149597870.7),
                      'distance_ld': round(float(p['dist']) * 149597870.7 / 384400, 2),
                      'speed_kms': round(float(p['v_rel']), 2), 'time_uncertainty': p.get('t_sigma_f')})
    return {'items': items, 'window_days': 30}


def events():
    payload = get_json('https://eonet.gsfc.nasa.gov/api/v3/events', {'status': 'open', 'days': 30, 'limit': 60})
    items = []
    for p in payload['events']:
        geometries = sorted(p.get('geometry', []), key=lambda g: g.get('date', ''))
        if not geometries:
            continue
        g = geometries[-1]
        items.append({'id': p['id'], 'title': plain(p['title']), 'categories': p.get('categories', []),
                      'date': g.get('date'), 'geometry': g,
                      'url': next((safe_url(s.get('url')) for s in p.get('sources', []) if safe_url(s.get('url'))), '')})
    return {'items': items}


def weather():
    today = datetime.now(timezone.utc).date()
    payload = get_json('https://ccmc.gsfc.nasa.gov/DONKI-API/get/FLR', {'startDate': str(today - timedelta(days=7)), 'endDate': str(today)})
    if not isinstance(payload, list):
        raise ValueError('Нет данных DONKI')
    return {'items': [{'date': p.get('peakTime') or p.get('beginTime'), 'class': p.get('classType'), 'url': safe_url(p.get('link'))} for p in payload]}


SOURCES = {'apod': (apod, 3600, 'NASA APOD'), 'media': (media, 3600, 'NASA Image Library'),
           'rover': (rover, 1800, 'Nebulum One / NASA'), 'epic': (epic, 3600, 'NASA EPIC'),
           'asteroids': (asteroids, 21600, 'NASA JPL'), 'events': (events, 1800, 'NASA EONET'),
           'weather': (weather, 1800, 'NASA DONKI'), 'asset': (asset, 86400, 'NASA Image Library')}


def _read(path):
    try:
        value = json.loads(path.read_text())
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def _refresh(key, path, source, args):
    try:
        data = SOURCES[source][0](*args)
        entry = {'data': data, 'updated_at': datetime.now(timezone.utc).isoformat(), 'timestamp': time.time(), 'error': None}
    except Exception as exc:
        log.warning('Source %s unavailable: %s', source, type(exc).__name__)
        entry = _read(path)
        entry['error'] = 'Источник временно недоступен. Повторим запрос через несколько минут.'
        if isinstance(exc, ValueError) and 'страницу' in str(exc):
            entry['error'] = 'Источник вернул веб-страницу вместо данных. Последний запрос не удался.'
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix('.tmp')
        tmp.write_text(json.dumps(entry), encoding='utf-8')
        tmp.replace(path)
        with _lock:
            files = sorted(CACHE_DIR.glob('*.json'), key=lambda p: p.stat().st_mtime)
            for old in files[:-MAX_ENTRIES]:
                if old.stem not in _pending:
                    old.unlink(missing_ok=True)
    except OSError:
        log.exception('Cannot persist source cache')
    finally:
        with _lock:
            _pending.discard(key)
            _retry[key] = time.time() + (300 if entry.get('error') else 0)
            if len(_retry) > MAX_ENTRIES * 2:
                for k in list(_retry):
                    if _retry[k] < time.time():
                        _retry.pop(k, None)


def snapshot(source, *args):
    """Never block an HTTP worker on upstream I/O; keep last successful data."""
    key = hashlib.sha256(json.dumps([source, args]).encode()).hexdigest()
    path = CACHE_DIR / f'{key}.json'
    entry = _read(path)
    expired = time.time() - entry.get('timestamp', 0) >= SOURCES[source][1]
    with _lock:
        if expired and key not in _pending and time.time() >= _retry.get(key, 0) and len(_pending) < 12:
            _pending.add(key)
            _pool.submit(_refresh, key, path, source, args)
        refreshing = key in _pending
    available = 'data' in entry
    return {'source': SOURCES[source][2], 'data': entry.get('data'), 'updated_at': entry.get('updated_at'),
            'status': ('stale' if expired or entry.get('error') else 'ready') if available else ('error' if entry.get('error') else 'loading'),
            'refreshing': refreshing, 'error': entry.get('error')}


def prime():
    for source, args in [('apod', ()), ('rover', ('curiosity',)), ('epic', ('natural', '')),
                         ('asteroids', ()), ('events', ()), ('weather', ()), ('media', ('Webb galaxy', 1, 'webb'))]:
        snapshot(source, *args)
