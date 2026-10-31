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
