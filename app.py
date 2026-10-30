#!/usr/bin/env python3
import sys
from legenda.ui import App, Gtk, Gdk

if __name__ == '__main__':
    Gtk.init()
    if Gdk.Display.get_default() is None:
        print('Não foi possível conectar ao display gráfico.', file=sys.stderr)
        raise SystemExit(1)
    raise SystemExit(App(smoke='--smoke-test' in sys.argv).run([sys.argv[0]]))
