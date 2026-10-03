import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import nasa_hub as hub
from web_server import app


class HubTests(unittest.TestCase):
    def test_new_apod_uses_hdurl_and_strips_markup(self):
        data = hub.normalize_apod([{'date':'2026-10-03','title':'A &amp; B','url':'https://science.nasa.gov/article/', 'hdurl':'https://assets.science.nasa.gov/photo.jpg','media_type':'image','explanation':'<strong>Hello</strong> world'}])
        self.assertEqual(data['image_url'],'https://assets.science.nasa.gov/photo.jpg')
        self.assertEqual(data['url'],'https://science.nasa.gov/article/')
        self.assertEqual(data['explanation'],'Hello world')
        self.assertEqual(data['title'],'A & B')

    def test_html_redirect_is_not_success(self):
        with patch('requests.get',return_value=Mock(headers={'Content-Type':'text/html'}, json=Mock(side_effect=ValueError('HTML')))):
            with self.assertRaisesRegex(ValueError,'страницу'):
                hub.get_json('https://example.org')

    def test_json_with_incorrect_content_type(self):
        with patch('requests.get', return_value=Mock(headers={'Content-Type':'application/rss+xml'}, json=Mock(return_value={'events':[]}))):
            self.assertEqual(hub.get_json('https://example.org'), {'events':[]})

    def test_failure_preserves_last_success(self):
        with tempfile.TemporaryDirectory() as d, patch.object(hub,'CACHE_DIR',Path(d)):
            path=Path(d)/'test.json'
            original={'data':{'items':[1]},'timestamp':1,'updated_at':'2026-10-01'}
            path.write_text(json.dumps(original))
            with patch.dict(hub.SOURCES,{'test':(Mock(side_effect=ValueError('offline')),60,'Test')}):
                hub._refresh('test',path,'test',())
            saved=json.loads(path.read_text())
            self.assertEqual(saved['data'],original['data'])
            self.assertEqual(saved['updated_at'],original['updated_at'])
            self.assertTrue(saved['error'])

    def test_slow_source_does_not_block_and_deduplicates(self):
        entered,release=threading.Event(),threading.Event()
        def slow():
            entered.set();release.wait(3);return {'items':[]}
        with tempfile.TemporaryDirectory() as d, patch.object(hub,'CACHE_DIR',Path(d)), patch.dict(hub.SOURCES,{'testslow':(slow,60,'Test')}):
            first=hub.snapshot('testslow')
            try:
                self.assertTrue(entered.wait(1))
                second=hub.snapshot('testslow')
                self.assertEqual(first['status'],'loading')
                self.assertTrue(second['refreshing'])
                with hub._lock:
                    self.assertEqual(len(hub._pending),1)
            finally:
                release.set()
                # Wait for this refresh to finish before removing the temporary cache.
                hub._pool.submit(lambda:None).result(timeout=4)
                import time
                for _ in range(100):
                    if not hub._pending:break
                    time.sleep(.01)

    def test_epic_paths_use_observation_date(self):
        with patch.object(hub,'get_json',return_value=[{'image':'epic_123','date':'2026-09-28 01:00:00'}]):
            item=hub.epic('natural')['items'][0]
            self.assertIn('/2026/09/28/jpg/epic_123.jpg',item['image_url'])

    def test_jpl_field_order_and_unit_conversion(self):
        with patch.object(hub,'get_json',return_value={'fields':['v_rel','des','dist','cd','t_sigma_f'],'data':[['10','Rock','1','2026-Oct-04','00:01']]}):
            item=hub.asteroids()['items'][0]
            self.assertEqual(item['distance_km'],149597871)
            self.assertEqual(item['speed_kms'],10)

    def test_routes_validate_inputs_without_upstream_calls(self):
        with app.test_client() as client, patch.object(hub,'get_json',side_effect=AssertionError('network')):
            for path in ['/api/explore/unknown','/api/explore/rover?rover=../a','/api/explore/epic?collection=../a','/api/explore/epic?date=2026-02-30','/api/explore/epic?date=2999-01-01','/api/explore/media?q=']:
                with self.subTest(path=path):self.assertIn(client.get(path).status_code,(400,404))
            self.assertEqual(client.get('/').status_code,200)
            self.assertEqual(client.get('/healthz').status_code,200)

    def test_untrusted_links_are_rejected(self):
        self.assertEqual(hub.safe_url('javascript:alert(1)'),'')
        self.assertEqual(hub.safe_url('//evil.test'),'')

if __name__=='__main__':unittest.main()
