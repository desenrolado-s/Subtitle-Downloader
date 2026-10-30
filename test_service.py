"""Regression tests for the service consumed by GTK."""
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from legenda import service

class ServiceTests(unittest.TestCase):
    def test_title_search_without_video(self):
        with patch('legenda.service.api', return_value={'data': []}) as api:
            self.assertEqual(service.search('Dune', None, 'pt-br', 'key'), [])
        self.assertIn('query=Dune', api.call_args.args[0])
        self.assertNotIn('moviehash', api.call_args.args[0])

    def test_hash_miss_falls_back_to_title(self):
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / 'movie.mkv'
            video.write_bytes(b'\0' * 131072)
            with patch('legenda.service.api', side_effect=[{'data': []}, {'data': [{'attributes': {'files': [{'file_id': 5}]}}]}]) as api:
                rows = service.search('movie', video, 'en', 'key')
            self.assertEqual(rows[0][0]['file_id'], 5)
            self.assertIn('moviehash=', api.call_args_list[0].args[0])
            self.assertIn('query=movie', api.call_args_list[1].args[0])

    def test_download_saves_srt(self):
        content = b'1\n00:00:01,000 --> 00:00:02,000\nHello\n'
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'movie.srt'
            with patch('legenda.service.api', side_effect=[{'token': 'session'}, {'link': 'https://example.org/sub'}]), patch('urllib.request.urlopen', return_value=io.BytesIO(content)):
                service.download(5, target, 'key', 'user', 'password')
            self.assertEqual(target.read_bytes(), content)

    def test_insecure_link_rejected(self):
        with patch('legenda.service.api', side_effect=[{'token': 'session'}, {'link': 'http://example.org/sub'}]):
            with self.assertRaises(ValueError):
                service.download(5, Path('unused.srt'), 'key', 'user', 'password')
