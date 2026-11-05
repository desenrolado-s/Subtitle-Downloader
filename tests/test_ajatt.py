import io
import unittest
import urllib.error
from unittest.mock import patch

from legenda import ajatt


class AjattTests(unittest.TestCase):
    def test_ignores_non_japanese_language(self):
        with patch('legenda.ajatt._links') as links:
            self.assertEqual(ajatt.search('One Piece', None, 'pt-br'), [])
        links.assert_not_called()

    def test_search_returns_srt_from_matching_anime_page(self):
        catalog = [('anime_tv/one-piece.html', 'ONE PIECE'), ('anime_tv/naruto.html', 'Naruto')]
        page = [('https://raw.githubusercontent.com/Ajatt-Tools/kitsunekko-mirror/main/subtitles/anime_tv/ONE%20PIECE/One%20Piece%20-%20E01.srt', 'One Piece - E01.srt'), ('episode.ass', 'Episode.ass')]
        with patch('legenda.ajatt._links', side_effect=[catalog, page]):
            rows = ajatt.search('One Piece', None, 'ja')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0]['provider'], 'ajatt')
        self.assertEqual(rows[0][1]['source'], 'AJATT / Kitsunekko')

    def test_rejects_untrusted_download_origin(self):
        with self.assertRaises(ValueError):
            ajatt.download({'download_url': 'https://example.invalid/file.srt'})
        with self.assertRaises(ValueError):
            ajatt.download({'download_url': 'https://raw.githubusercontent.com/other/source/main/file.srt'})

    def test_download_uses_allowed_https_url(self):
        url = 'https://raw.githubusercontent.com/Ajatt-Tools/kitsunekko-mirror/main/subtitles/x.srt'
        with patch('urllib.request.urlopen', return_value=io.BytesIO(b'subtitle')) as urlopen:
            self.assertEqual(ajatt.download({'download_url': url}), b'subtitle')
        self.assertEqual(urlopen.call_args.args[0].full_url, url)

    def test_catalog_network_error_is_clear(self):
        with patch('urllib.request.urlopen', side_effect=urllib.error.URLError('offline')):
            with self.assertRaisesRegex(RuntimeError, 'conectar ao catálogo'):
                ajatt._links(ajatt.CATALOG)
