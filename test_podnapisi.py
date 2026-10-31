import io
import unittest
import zipfile
from unittest.mock import patch

from legenda import podnapisi


class PodnapisiTests(unittest.TestCase):
    def test_search_parses_public_xml_results(self):
        xml = b'''<results><subtitle><pid>42</pid><release>Show.S01E02.srt</release><language>26</language><downloads>7</downloads></subtitle></results>'''
        with patch('legenda.podnapisi._fetch', return_value=xml):
            rows = podnapisi.search('Show S01E02', None, 'pt-br')
        self.assertEqual(rows[0][0]['download_url'], 'https://www.podnapisi.net/subtitles/42/download')
        self.assertEqual(rows[0][1]['source'], 'Podnapisi')

    def test_search_rejects_xml_entities(self):
        with self.assertRaisesRegex(RuntimeError, 'XML inválida'):
            podnapisi._xml(b'<!DOCTYPE x [<!ENTITY x "x">]><x/>')

    def test_download_extracts_single_srt_from_zip(self):
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w') as zipped:
            zipped.writestr('subtitle.srt', b'1\n00:00:01,000 --> 00:00:02,000\nHello\n')
        with patch('legenda.podnapisi._fetch', return_value=archive.getvalue()):
            body = podnapisi.download({'download_url': 'https://www.podnapisi.net/subtitles/42/download'})
        self.assertIn(b'Hello', body)

    def test_download_rejects_off_origin_url(self):
        with self.assertRaises(ValueError):
            podnapisi.download({'download_url': 'https://example.invalid/file.srt'})
