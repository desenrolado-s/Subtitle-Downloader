"""Certificate-store setup for frozen Linux builds."""

import os
import sys
from pathlib import Path


def configure_ssl_certificates():
    """Point the bundled OpenSSL at the CA bundle shipped with the app.

    PyInstaller includes libssl in Linux builds.  Its compiled-in certificate
    location belongs to the build machine and is not available inside an
    AppImage, so HTTPS requests otherwise fail certificate verification.
    """
    if not getattr(sys, 'frozen', False):
        return None

    certificate_file = Path(sys._MEIPASS) / 'certs' / 'ca-certificates.crt'
    if not certificate_file.is_file():
        return None

    # Preserve an explicit choice made by a user or corporate environment.
    os.environ.setdefault('SSL_CERT_FILE', str(certificate_file))
    return certificate_file
