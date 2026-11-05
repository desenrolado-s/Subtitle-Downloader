#!/usr/bin/env bash
set -euo pipefail

dest=${1:?usage: bundle-gtk-typelibs.sh DEST_DIR}
mkdir -p "$dest"

search_dirs=()
IFS=: read -r -a env_dirs <<< "${GI_TYPELIB_PATH:-}"
for dir in "${env_dirs[@]}" /usr/lib64/girepository-1.0 /usr/lib/girepository-1.0 /usr/lib/x86_64-linux-gnu/girepository-1.0; do
  [ -n "$dir" ] && [ -d "$dir" ] || continue
  case " ${search_dirs[*]-} " in
    *" $dir "*) ;;
    *) search_dirs+=("$dir") ;;
  esac
done

# GTK 4 and the namespaces it needs at runtime.  Bundling these makes the
# application independent from the distribution's typelib packages, which are
# often split from the GTK libraries (for example on openSUSE).
typelibs=(
  Gtk-4.0 Gdk-4.0 Gsk-4.0 GdkX11-4.0 GdkWayland-4.0
  Graphene-1.0 Pango-1.0 PangoCairo-1.0 cairo-1.0
  GdkPixbuf-2.0 GModule-2.0 freetype2-2.0 HarfBuzz-0.0
  GLib-2.0 GObject-2.0 Gio-2.0 GioUnix-2.0 xlib-2.0
)
required=(Gtk-4.0 Gdk-4.0 Gsk-4.0 Graphene-1.0)

for name in "${typelibs[@]}"; do
  for dir in "${search_dirs[@]}"; do
    if [ -f "$dir/$name.typelib" ]; then
      cp -f "$dir/$name.typelib" "$dest/"
      break
    fi
  done
done

for name in "${required[@]}"; do
  if [ ! -s "$dest/$name.typelib" ]; then
    echo "Missing required GTK typelib: $name" >&2
    echo "Searched: ${search_dirs[*]}" >&2
    exit 1
  fi
done

# The Linux build runs on Ubuntu 22.04, whose GTK 4.6 typelib predates
# Gtk.FileDialog (added in GTK 4.10). Bundle newer introspection metadata
# while continuing to use the host GTK libraries at runtime. This lets newer
# distributions use Gtk.FileDialog without shipping GTK shared libraries.
gtk_typelib_version=4.14.5+ds-0ubuntu0.10
gtk_typelib_package="gir1.2-gtk-4.0_${gtk_typelib_version}_amd64.deb"
gtk_typelib_url="https://archive.ubuntu.com/ubuntu/pool/main/g/gtk4/${gtk_typelib_package}"
gtk_typelib_sha256=027a65ddf6a652b92ca746d2f9b5f80178df0fc3d7f29a84115a5640f1dddc45
gtk_typelib_cache="build/gtk-typelibs-${gtk_typelib_version}"
gtk_typelib_archive="$gtk_typelib_cache/$gtk_typelib_package"
gtk_typelib_root="$gtk_typelib_cache/root"
if [ ! -s "$gtk_typelib_archive" ]; then
  mkdir -p "$gtk_typelib_cache"
  curl --fail --location --retry 3 "$gtk_typelib_url" --output "$gtk_typelib_archive"
fi
printf '%s  %s\n' "$gtk_typelib_sha256" "$gtk_typelib_archive" | sha256sum --check --status
if [ ! -d "$gtk_typelib_root" ]; then
  mkdir -p "$gtk_typelib_root"
  dpkg-deb --extract "$gtk_typelib_archive" "$gtk_typelib_root"
fi
for name in Gtk-4.0 Gdk-4.0 Gsk-4.0 GdkWayland-4.0 GdkX11-4.0; do
  newer_typelib="$gtk_typelib_root/usr/lib/x86_64-linux-gnu/girepository-1.0/$name.typelib"
  if [ -s "$newer_typelib" ]; then
    cp -f "$newer_typelib" "$dest/$name.typelib"
  fi
done
if ! strings "$dest/Gtk-4.0.typelib" | grep -qx 'GtkFileDialog'; then
  echo 'Bundled Gtk-4.0 typelib does not expose Gtk.FileDialog.' >&2
  exit 1
fi
