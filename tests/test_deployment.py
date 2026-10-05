import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import bootstrap
import comments
import config
import nasa_api
import nasa_apod
import nasa_epic
from web_server import app


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.addCleanup(nasa_api._record_success)
        nasa_api._record_success()

    def test_bootstrap_returns_during_blocked_sync_and_runs_once(self):
        entered, release = threading.Event(), threading.Event()
        def blocked():
            entered.set()
            release.wait(3)
        with patch.object(bootstrap, '_background_thread', None), \
             patch.object(bootstrap, 'ensure_directories'), \
             patch.object(comments, 'init_db'), \
             patch.object(bootstrap, 'run_initial_sync', side_effect=blocked) as sync, \
             patch.object(bootstrap, 'start_services') as services:
            worker = bootstrap.bootstrap()
            try:
                self.assertTrue(entered.wait(1))
                self.assertIs(bootstrap.bootstrap(), worker)
                self.assertTrue(worker.is_alive())
                with app.test_client() as client:
                    self.assertEqual(client.get('/healthz').status_code, 200)
                services.assert_not_called()
            finally:
                release.set()
                worker.join(3)
            sync.assert_called_once()
            services.assert_called_once()

    def test_retry_after_is_not_shortened(self):
        for header, expected in [('3600', 4600), ('Thu, 01 Jan 1970 01:16:40 GMT', 4600), ('invalid', 4600)]:
            with self.subTest(header=header):
                nasa_api._record_success()
                response = Mock(status_code=429, headers={'Retry-After': header})
                with patch('nasa_api.requests.get', return_value=response) as get, patch('nasa_api.time.time', return_value=1000):
                    self.assertEqual(nasa_api.fetch_and_save_photos(), 0)
                    self.assertEqual(nasa_api._backoff_until, expected)
                    nasa_api.fetch_and_save_photos()
                    get.assert_called_once()

    def test_latest_rover_and_explicit_date(self):
        response = Mock(status_code=200)
        response.json.return_value = {'latest_photos': [{'id': 1}]}
        with patch('nasa_api.requests.get', return_value=response) as get:
            nasa_api.get_mars_rover_photos()
            self.assertTrue(get.call_args.args[0].endswith('/curiosity/latest_photos'))
            self.assertNotIn('sol', get.call_args.kwargs['params'])
            nasa_api.get_mars_rover_photos('spirit', '2010-01-01')
            self.assertTrue(get.call_args.args[0].endswith('/spirit/photos'))
            self.assertEqual(get.call_args.kwargs['params']['earth_date'], '2010-01-01')

    def test_epic_download_has_timeout(self):
        with patch('nasa_epic.requests.get', return_value=Mock(status_code=200, content=b'image')) as get:
            path = nasa_epic.download_epic_photo({'image': 'test', 'date': '2026-10-01 00:00:00'}, self.directory)
            self.assertTrue(Path(path).is_file())
            self.assertEqual(get.call_args.kwargs['timeout'], (5, 30))

    def test_apod_cache_is_paired_and_routes_are_offline(self):
        data = {'title': 'Title / unsafe', 'date': '2026-10-01', 'media_type': 'image', 'image_url': 'https://example.org/a.jpg?size=2', 'explanation': 'Description'}
        with patch('nasa_apod.get_apod', return_value=data), patch('nasa_apod.requests.get', return_value=Mock(content=b'image', headers={'Content-Type':'image/jpeg'})):
            path, _ = nasa_apod.download_apod(self.directory)
        self.assertEqual(Path(path).parent, self.directory)
        with patch.object(config, 'NASA_APOD_DIR', self.directory), patch.object(comments, 'get_comments', return_value=[]), patch('requests.get', side_effect=AssertionError('Unexpected network call')):
            with app.test_client() as client:
                response = client.get('/classic')
                self.assertEqual(response.status_code, 200)
                self.assertIn(b'Title / unsafe', response.data)
                self.assertEqual(client.get('/apod/data').json['date'], data['date'])
                self.assertEqual(client.get('/healthz').status_code, 200)
            with patch('nasa_apod.get_apod', return_value=None):
                nasa_apod.download_apod(self.directory)
            self.assertEqual(nasa_apod.get_cached_apod()['date'], data['date'])

    def test_video_and_corrupt_cache(self):
        video = {'media_type': 'video', 'date': '2026-10-02', 'url': 'https://example.org/video'}
        with patch('nasa_apod.get_apod', return_value=video), patch('requests.get') as get:
            nasa_apod.download_apod(self.directory)
            get.assert_not_called()
        self.assertEqual(nasa_apod.get_cached_apod(self.directory)['media_type'], 'video')
        (self.directory / 'metadata.json').write_text('{broken')
        self.assertIsNone(nasa_apod.get_cached_apod(self.directory))


if __name__ == '__main__':
    unittest.main()
