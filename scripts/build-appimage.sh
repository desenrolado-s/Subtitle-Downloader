#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
test -x dist/Legenda/Legenda
mkdir -p build/Legenda.AppDir/usr/Legenda
cp -a dist/Legenda/. build/Legenda.AppDir/usr/Legenda/
# The bundled OpenSSL cannot rely on a certificate path from the build host.
bash scripts/bundle-ca-certificates.sh build/Legenda.AppDir/usr/Legenda/_internal
# Ship GTK typelibs so the AppImage does not require the distribution's
# typelib packages (openSUSE keeps them separate from the GTK libraries).
bash scripts/bundle-gtk-typelibs.sh build/Legenda.AppDir/usr/Legenda/_internal/gi_typelibs
# GI uses the host GTK/GLib stack.  Keeping the Ubuntu copies of these base
# libraries makes the AppImage incompatible with newer distributions.
find build/Legenda.AppDir \( -name "libglib-2.0.so*" -o -name "libgobject-2.0.so*" -o -name "libgio-2.0.so*" -o -name "libgmodule-2.0.so*" -o -name "libgirepository-*.so*" -o -name "libmount.so*" -o -name "libblkid.so*" -o -name "libuuid.so*" -o -name "libsystemd.so*" -o -name "libudev.so*" \) -delete
rm -rf build/Legenda.AppDir/usr/Legenda/_internal/gio_modules build/Legenda.AppDir/usr/Legenda/gio_modules
# AppImage Manager reads this AppImage-specific desktop entry to display the version.
APPIMAGE_VERSION=${APPIMAGE_VERSION:-$(git describe --tags --always 2>/dev/null || printf '0.0.0')}
sed "s/^Categories=/X-AppImage-Version=${APPIMAGE_VERSION}\\nCategories=/" packaging/linux/legenda.desktop > build/Legenda.AppDir/legenda.desktop
cp packaging/linux/legenda.png build/Legenda.AppDir/
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
UPDATE_INFO=${APPIMAGE_UPDATE_INFO:-"zsync|https://github.com/desenrolado-s/Subtitle-Downloader/releases/latest/download/Legenda-linux-x64.AppImage.zsync"}
ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 build/appimagetool.AppImage -u "$UPDATE_INFO" build/Legenda.AppDir Legenda-linux-x64.AppImage
# The release workflow regenerates this file with the final asset name.
rm -f Legenda-linux-x64.AppImage.zsync
