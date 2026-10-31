"""GTK integration checks; run with a graphical display or xvfb-run."""
import sys
import unittest
from unittest.mock import patch
from uuid import uuid4

# GitHub's Windows runners do not expose an interactive desktop to GTK.  The
# executable is still built there; UI integration is covered on Linux/macOS.
if sys.platform == 'win32':
    raise unittest.SkipTest('GTK integration tests require an interactive Windows desktop')

try:
    from legenda.ui import App, Gtk, Gdk
except ModuleNotFoundError as error:
    if error.name != 'gi':
        raise
    raise unittest.SkipTest('GTK integration tests require PyGObject')

Gtk.init()

@unittest.skipUnless(Gdk.Display.get_default(), 'Requires a graphical display')
class GtkTests(unittest.TestCase):
    def setUp(self):
        self.app = App()
        # quit() does not unregister apps registered without running their loop.
        # Keep real D-Bus registration, but isolate each test's exported objects.
        self.app.set_application_id(f'io.github.desenrolado_s.Legenda.Test{uuid4().hex}')
        self.vault_patch = patch("legenda.ui.credentials.load", return_value=None)
        self.vault_patch.start()
        self.addCleanup(self.vault_patch.stop)
        self.app.register(None)
        self.app.activate()
        self.app.run_task = lambda work, done: done(work())

    def tearDown(self):
        if getattr(self.app, 'account', None):
            self.app.account.destroy()
        self.app.window.destroy()
        self.app.quit()

    def test_title_search_populates_rows(self):
        self.app.query.set_text('Dune')
        self.app.key.set_text('key')
        result = [({'file_id': 1, 'file_name': 'Dune.srt'}, {'language': 'pt-br'})]
        with patch('legenda.ui.service.search', return_value=result) as search:
            self.app.search()
        search.assert_called_once_with('Dune', None, 'pt-br', 'key')
        self.assertIsNotNone(self.app.list.get_row_at_index(0))
        self.assertEqual(self.app.results, result)

    def test_account_window_can_reopen(self):
        self.app.settings()
        self.app.key.set_text('session-key')
        self.app.account.hide()
        self.app.settings()
        self.assertTrue(self.app.account.get_visible())
        self.assertEqual(self.app.key.get_text(), 'session-key')

    def test_invalid_query_stops_request(self):
        with patch('legenda.ui.service.search') as search:
            self.app.search()
        search.assert_not_called()

    def test_keyless_episode_search_is_allowed(self):
        self.app.query.set_text('The Show S01E02')
        result = [({'provider': 'gestdown', 'download_url': 'https://api.gestdown.info/subtitles/download/x', 'file_name': 'The Show S01E02'}, {'language': 'pt-br', 'source': 'Gestdown (Addic7ed)'})]
        with patch('legenda.ui.service.search', return_value=result) as search:
            self.app.search()
        search.assert_called_once_with('The Show S01E02', None, 'pt-br', '')
        self.assertIsNotNone(self.app.list.get_row_at_index(0))
