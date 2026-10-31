import io
import unittest
from unittest.mock import patch

from legenda import subtitulamos


class SubtitulamosTests(unittest.TestCase):
    def test_ignores_unsupported_language(self):
        with patch('legenda.subtitulamos._episode_url') as episode_url:
            self.assertEqual(subtitulamos.search('Show S01E02', None, 'ja'), [])
        episode_url.assert_not_called()

    def test_search_finds_portuguese_finished_subtitle(self):
        page = b'''<div class="subtitle_language">Brazilian</div>
        <div id="progress_buttons_row"><div><a href="/download/subtitle.srt">Baixar</a></div></div>
        <div class="subtitle_language">English</div>
        <div id="progress_buttons_row"><span>Em andamento</span></div>'''
        with patch('legenda.subtitulamos._episode_url', return_value='https://www.subtitulamos.tv/episodes/42'), patch('legenda.subtitulamos._request', return_value=page):
            rows = subtitulamos.search('The Show S01E02', None, 'pt-br')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0]['provider'], 'subtitulamos')
        self.assertEqual(rows[0][0]['download_url'], 'https://www.subtitulamos.tv/download/subtitle.srt')
        self.assertEqual(rows[0][1]['source'], 'Subtitulamos.tv')

    def test_download_rejects_off_origin_url(self):
        with self.assertRaises(ValueError):
            subtitulamos.download({'download_url': 'https://example.invalid/file.srt'})

    def test_download_uses_allowed_https_url(self):
        url = 'https://www.subtitulamos.tv/download/file.srt'
        with patch('urllib.request.urlopen', return_value=io.BytesIO(b'subtitle')) as urlopen:
            self.assertEqual(subtitulamos.download({'download_url': url}), b'subtitle')
        self.assertEqual(urlopen.call_args.args[0].full_url, url)
