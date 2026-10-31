#!/usr/bin/env python3
import sys
from legenda.certificates import configure_ssl_certificates

# Must run before importing GTK/urllib.  The frozen AppImage carries OpenSSL
# but not the build machine's certificate path.
configure_ssl_certificates()

from legenda.ui import App, Gtk, Gdk

if __name__ == '__main__':
    Gtk.init()
    if Gdk.Display.get_default() is None:
        print('Não foi possível conectar ao display gráfico.', file=sys.stderr)
        raise SystemExit(1)
    raise SystemExit(App(smoke='--smoke-test' in sys.argv).run([sys.argv[0]]))
