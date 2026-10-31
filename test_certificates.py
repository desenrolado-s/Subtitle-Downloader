import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from legenda.certificates import configure_ssl_certificates


class CertificateTests(unittest.TestCase):
    def test_frozen_app_uses_its_bundled_ca_file(self):
        with tempfile.TemporaryDirectory() as directory:
            certificate = Path(directory) / 'certs' / 'ca-certificates.crt'
            certificate.parent.mkdir()
            certificate.write_text('certificate')
            with patch('legenda.certificates.sys.frozen', True, create=True), \
                 patch('legenda.certificates.sys._MEIPASS', directory, create=True), \
                 patch.dict(os.environ, {}, clear=True):
                self.assertEqual(configure_ssl_certificates(), certificate)
                self.assertEqual(os.environ['SSL_CERT_FILE'], str(certificate))

    def test_explicit_certificate_file_is_not_overridden(self):
        with tempfile.TemporaryDirectory() as directory:
            certificate = Path(directory) / 'certs' / 'ca-certificates.crt'
            certificate.parent.mkdir()
            certificate.write_text('certificate')
            with patch('legenda.certificates.sys.frozen', True, create=True), \
                 patch('legenda.certificates.sys._MEIPASS', directory, create=True), \
                 patch.dict(os.environ, {'SSL_CERT_FILE': '/custom/cert.pem'}, clear=True):
                configure_ssl_certificates()
                self.assertEqual(os.environ['SSL_CERT_FILE'], '/custom/cert.pem')
