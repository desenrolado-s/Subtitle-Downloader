import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
import urllib.error
from legenda import legacy_ui as app
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

    def test_search_download_flow(self):
        # Exercise the actual UI callbacks without a display, with provider responses simulated.
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / 'movie.mkv'
            video.write_bytes(b'small video')
            ui = app.App.__new__(app.App)
            ui.busy = False
            for name, value in [('video', str(video)), ('key', 'key'), ('lang', 'pt-br'),
                                ('query', 'movie'), ('user', 'user'), ('password', 'password')]:
                setattr(ui, name, Mock(get=Mock(return_value=value)))
            ui.tree = Mock()
            ui.tree.get_children.return_value = []
            ui.tree.selection.return_value = ['0']
            ui.status = Mock()
            ui.run = lambda work, done: done(work())
            response = {'data': [{'attributes': {'language': 'pt-br', 'download_count': 4,
                        'files': [{'file_id': 42, 'file_name': 'movie.srt'}]}}]}
            with patch('legenda.legacy_ui.api', return_value=response):
                ui.search()
            self.assertEqual(len(ui.results), 1)
            with patch('legenda.legacy_ui.api', side_effect=[{'token': 'token'}, {'link': 'https://example.org/sub.srt'}]) as api_call:
                with patch('urllib.request.urlopen', return_value=io.BytesIO(SRT)):
                    ui.download()
            self.assertEqual(video.with_suffix('.pt-br.srt').read_bytes(), SRT)
            self.assertEqual(api_call.call_args.args, ('download', 'key', {'file_id': 42, 'sub_format': 'srt'}, 'token'))

    def test_title_only_download_flow(self):
        # Exercise the actual UI callbacks without a display, with provider responses simulated.
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / 'movie.mkv'
            video.write_bytes(b'small video')
            ui = app.App.__new__(app.App)
            ui.busy = False
            for name, value in [('video', ''), ('key', 'key'), ('lang', 'pt-br'),
                                ('query', 'movie'), ('user', 'user'), ('password', 'password')]:
                setattr(ui, name, Mock(get=Mock(return_value=value)))
            ui.tree = Mock()
            ui.tree.get_children.return_value = []
            ui.tree.selection.return_value = ['0']
            ui.status = Mock()
            ui.run = lambda work, done: done(work())
            response = {'data': [{'attributes': {'language': 'pt-br', 'download_count': 4,
                        'files': [{'file_id': 42, 'file_name': 'movie.srt'}]}}]}
            with patch('legenda.legacy_ui.api', return_value=response):
                ui.search()
            self.assertEqual(len(ui.results), 1)
            with patch('legenda.legacy_ui.api', side_effect=[{'token': 'token'}, {'link': 'https://example.org/sub.srt'}]) as api_call:
                with patch('urllib.request.urlopen', return_value=io.BytesIO(SRT)), patch('legenda.legacy_ui.filedialog.asksaveasfilename', return_value=str(video.with_suffix('.pt-br.srt'))):
                    ui.download()
            self.assertEqual(video.with_suffix('.pt-br.srt').read_bytes(), SRT)
            self.assertEqual(api_call.call_args.args, ('download', 'key', {'file_id': 42, 'sub_format': 'srt'}, 'token'))

    def test_quota_error(self):
        error = urllib.error.HTTPError(BASE, 429, 'limit', {}, None)
        with patch('urllib.request.urlopen', side_effect=error):
            with self.assertRaisesRegex(RuntimeError, 'Muitas requisições'):
                api('subtitles', 'key')

if __name__ == '__main__':
    unittest.main()
