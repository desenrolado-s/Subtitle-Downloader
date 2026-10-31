import io
import unittest
from pathlib import Path
from unittest.mock import patch

from legenda import gestdown


class GestdownTests(unittest.TestCase):
    def test_episode_query_reads_standard_release_name(self):
        show, season, episode = gestdown.episode_query('', Path('The.Show.S02E03.1080p.mkv'))
        self.assertEqual((show, season, episode), ('The Show', 2, 3))

    def test_search_ignores_incomplete_and_off_origin_results(self):
        responses = [
            {'shows': [{'id': 'show-id', 'name': 'The Show'}]},
            {'matchingSubtitles': [
                {'subtitleId': 'good', 'downloadUri': '/subtitles/download/good', 'version': 'WEB', 'completed': True, 'downloadCount': 4},
                {'subtitleId': 'bad', 'downloadUri': 'https://example.invalid/sub', 'completed': True},
                {'subtitleId': 'partial', 'downloadUri': '/subtitles/download/partial', 'completed': False},
            ]},
        ]
        with patch('legenda.gestdown._json', side_effect=responses):
            rows = gestdown.search('The Show S01E02', None, 'pt-br')
        self.assertEqual([row[0]['subtitle_id'] for row in rows], ['good'])

    def test_search_builds_result(self):
        responses = [
            {'shows': [{'id': 'show-id', 'name': 'The Show'}]},
            {'matchingSubtitles': [{'subtitleId': 'good', 'downloadUri': '/subtitles/download/good', 'version': 'WEB', 'completed': True, 'downloadCount': 4}]},
        ]
        with patch('legenda.gestdown._json', side_effect=responses):
            rows = gestdown.search('The Show S01E02', None, 'pt-br')
        self.assertEqual(rows[0][0]['download_url'], 'https://api.gestdown.info/subtitles/download/good')
        self.assertEqual(rows[0][1]['source'], 'Gestdown (Addic7ed)')

    def test_download_uses_https_url(self):
        with patch('urllib.request.urlopen', return_value=io.BytesIO(b'subtitle')) as urlopen:
            self.assertEqual(gestdown.download({'download_url': 'https://api.gestdown.info/subtitles/download/x'}), b'subtitle')
        self.assertEqual(urlopen.call_args.args[0].full_url, 'https://api.gestdown.info/subtitles/download/x')

    def test_download_rejects_off_origin_url(self):
        with self.assertRaises(ValueError):
            gestdown.download({'download_url': 'https://example.invalid/subtitle'})
