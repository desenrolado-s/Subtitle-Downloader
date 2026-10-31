#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
test -x dist/Legenda/Legenda
mkdir -p build/Legenda.AppDir/usr/Legenda
cp -a dist/Legenda/. build/Legenda.AppDir/usr/Legenda/
# GI uses the host GTK/GLib stack.  Keeping the Ubuntu copies of these base
# libraries makes the AppImage incompatible with newer distributions.
find build/Legenda.AppDir \( -name "libglib-2.0.so*" -o -name "libgobject-2.0.so*" -o -name "libgio-2.0.so*" -o -name "libgmodule-2.0.so*" -o -name "libgirepository-*.so*" -o -name "libmount.so*" -o -name "libblkid.so*" -o -name "libuuid.so*" -o -name "libsystemd.so*" -o -name "libudev.so*" \) -delete
rm -rf build/Legenda.AppDir/usr/Legenda/_internal/gio_modules build/Legenda.AppDir/usr/Legenda/gio_modules
cp packaging/linux/legenda.desktop packaging/linux/legenda.png build/Legenda.AppDir/
cp packaging/linux/legenda.png build/Legenda.AppDir/.DirIcon
test -s build/Legenda.AppDir/legenda.png
test -s build/Legenda.AppDir/.DirIcon
cat > build/Legenda.AppDir/AppRun <<'RUN'
#!/bin/sh
HERE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
for p in /usr/lib64/girepository-1.0 /usr/lib/girepository-1.0 /usr/lib/x86_64-linux-gnu/girepository-1.0; do
  [ -d "$p" ] && GI_TYPELIB_PATH="$p${GI_TYPELIB_PATH:+:$GI_TYPELIB_PATH}"
done
export GI_TYPELIB_PATH
exec "$HERE/usr/Legenda/Legenda" "$@"
RUN
chmod +x build/Legenda.AppDir/AppRun
curl --fail --location --retry 3 https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage -o build/appimagetool.AppImage
chmod +x build/appimagetool.AppImage
ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 build/appimagetool.AppImage build/Legenda.AppDir Legenda-linux-x64.AppImage
