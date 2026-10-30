import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import urllib.error
from legenda.provider import api, BASE
from legenda.files import save_subtitle, movie_hash

SRT = b'1\n00:00:01,000 --> 00:00:02,000\nOla!\n'

class Tests(unittest.TestCase):
    def test_save_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'movie.pt-br.srt'
            save_subtitle(path, SRT)
            self.assertEqual(path.read_bytes(), SRT)
            with self.assertRaises(FileExistsError):
                save_subtitle(path, SRT + b'changed')
            self.assertEqual(path.read_bytes(), SRT)
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_reject_html(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'movie.srt'
            with self.assertRaises(RuntimeError):
                save_subtitle(path, b'<html><!-- error -->Unavailable</html>')
            self.assertFalse(path.exists())

    def test_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'video'
            path.write_bytes(b'\0' * 131072)
            self.assertEqual(movie_hash(path), '0000000000020000')
            path.write_bytes(b'tiny')
            self.assertIsNone(movie_hash(path))

    def test_api_headers_and_payload(self):
        with patch('urllib.request.urlopen', return_value=io.BytesIO(b'{"token":"ok"}')) as request:
            self.assertEqual(api('login', 'key', {'username':'user'}, 'token')['token'], 'ok')
            req = request.call_args.args[0]
            self.assertEqual(req.get_header('Authorization'), 'Bearer token')
            self.assertEqual(req.get_header('Api-key'), 'key')
            self.assertEqual(req.get_method(), 'POST')

    def test_network_error(self):
        with patch('urllib.request.urlopen', side_effect=urllib.error.URLError('offline')):
            with self.assertRaisesRegex(RuntimeError, 'Confira a internet'):
                api('subtitles', 'key')

    def test_quota_error(self):
        error = urllib.error.HTTPError(BASE, 429, 'limit', {}, None)
        with patch('urllib.request.urlopen', side_effect=error):
            with self.assertRaisesRegex(RuntimeError, 'Muitas requisições'):
                api('subtitles', 'key')

if __name__ == '__main__':
    unittest.main()
