#!/usr/bin/env python3
"""Stage GTK DLLs referenced by the Windows GI typelibs for PyInstaller."""

from __future__ import annotations

import shutil
import sys
import xml.etree.ElementTree as ET
from collections import deque
from pathlib import Path

import pefile


PREFIX = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/ucrt64')
DEST = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('build/windows-gtk-binaries')
BIN_DIR = PREFIX / 'bin'
GIR_DIR = PREFIX / 'share/gir-1.0'
TYPELIB_DIR = PREFIX / 'lib/girepository-1.0'

# The namespaces used directly by GTK 4 and by its core dependencies.
NAMESPACES = (
    'Gtk-4.0', 'Gdk-4.0', 'GdkWin32-4.0', 'Gsk-4.0', 'Graphene-1.0',
    'Pango-1.0', 'PangoCairo-1.0', 'cairo-1.0', 'GdkPixbuf-2.0',
    'GModule-2.0', 'freetype2-2.0', 'HarfBuzz-0.0', 'GLib-2.0',
    'GObject-2.0', 'Gio-2.0', 'win32-1.0', 'xlib-2.0',
)
REQUIRED_TYPELIBS = {'Gtk-4.0', 'Gdk-4.0', 'Gsk-4.0', 'Graphene-1.0'}


def shared_libraries(gir_file: Path) -> list[str]:
    root = ET.parse(gir_file).getroot()
    return [
        name.strip()
        for element in root.iter()
        if element.tag.endswith('shared-library') and element.text
        for name in element.text.split(',')
        if name.strip()
    ]


def main() -> None:
    missing_typelibs = [name for name in REQUIRED_TYPELIBS if not (TYPELIB_DIR / f'{name}.typelib').is_file()]
    if missing_typelibs:
        raise SystemExit(f'Missing GTK typelibs: {", ".join(sorted(missing_typelibs))}')

    library_names: set[str] = set()
    for namespace in NAMESPACES:
        typelib = TYPELIB_DIR / f'{namespace}.typelib'
        gir_file = GIR_DIR / f'{namespace}.gir'
        if typelib.is_file() and gir_file.is_file():
            library_names.update(shared_libraries(gir_file))

    by_name = {path.name.casefold(): path for path in BIN_DIR.glob('*.dll')}
    pending = deque(sorted(library_names, key=str.casefold))
    selected: dict[str, Path] = {}
    unresolved: set[str] = set()

    while pending:
        name = pending.popleft()
        key = name.casefold()
        if key in selected or key in unresolved:
            continue
        dll = by_name.get(key)
        if dll is None:
            unresolved.add(name)
            continue

        selected[key] = dll
        pe = pefile.PE(str(dll), fast_load=True)
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
        for imported in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', []):
            dependency = imported.dll.decode('ascii', errors='ignore')
            if dependency.casefold() in by_name:
                pending.append(dependency)

    if unresolved:
        raise SystemExit(f'GTK typelib DLLs not found in {BIN_DIR}: {", ".join(sorted(unresolved))}')
    if not selected:
        raise SystemExit('No GTK runtime DLLs were found from the GTK typelibs.')

    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)
    for dll in selected.values():
        shutil.copy2(dll, DEST / dll.name)
    print(f'Staged {len(selected)} GTK runtime DLLs in {DEST}')


if __name__ == '__main__':
    main()
