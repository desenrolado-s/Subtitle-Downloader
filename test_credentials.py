import json
import unittest
from unittest.mock import patch, Mock
from legenda import credentials

class CredentialsTests(unittest.TestCase):
    def test_save_load_forget(self):
        vault = Mock()
        vault.get_password.return_value = None
        with patch('legenda.credentials.backend', return_value=vault):
            self.assertIsNone(credentials.load())
            credentials.save('key', 'user', 'secret')
            raw = vault.set_password.call_args.args[2]
            vault.get_password.return_value = raw
            self.assertEqual(credentials.load()['password'], 'secret')
            credentials.forget()
            vault.delete_password.assert_called_once_with(credentials.SERVICE, credentials.ACCOUNT)

    def test_failure_has_no_fallback(self):
        with patch('legenda.credentials.backend', side_effect=RuntimeError('locked')):
            with self.assertRaises(RuntimeError):
                credentials.save('key', 'user', 'secret')
