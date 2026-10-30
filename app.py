#!/usr/bin/env python3
"""Desktop entry point, also used by PyInstaller."""
import sys

def main():
    from legenda.ui import App
    import tkinter as tk
    root = tk.Tk()
    App(root)
    if '--smoke-test' in sys.argv:
        root.update()
        root.destroy()
    else:
        root.mainloop()

if __name__ == '__main__':
    main()
