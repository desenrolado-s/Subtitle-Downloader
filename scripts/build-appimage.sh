#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
test -x dist/Legenda/Legenda
mkdir -p build/Legenda.AppDir/usr/Legenda
cp -a dist/Legenda/. build/Legenda.AppDir/usr/Legenda/
cp packaging/linux/legenda.desktop packaging/linux/legenda.svg build/Legenda.AppDir/
cat > build/Legenda.AppDir/AppRun <<'RUN'
#!/bin/sh
HERE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
exec "$HERE/usr/Legenda/Legenda" "$@"
RUN
chmod +x build/Legenda.AppDir/AppRun
curl --fail --location --retry 3 https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage -o build/appimagetool.AppImage
chmod +x build/appimagetool.AppImage
ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 build/appimagetool.AppImage build/Legenda.AppDir Legenda-linux-x64.AppImage
