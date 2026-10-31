#!/usr/bin/env bash
set -euo pipefail

destination=${1:?Usage: bundle-ca-certificates.sh DESTINATION_DIRECTORY}
for certificate_file in \
  /etc/ssl/certs/ca-certificates.crt \
  /etc/pki/tls/certs/ca-bundle.crt \
  /etc/ssl/ca-bundle.pem; do
  if [ -r "$certificate_file" ]; then
    mkdir -p "$destination/certs"
    # Dereference distro symlinks: the AppImage must contain the actual bundle.
    cp -L "$certificate_file" "$destination/certs/ca-certificates.crt"
    test -s "$destination/certs/ca-certificates.crt"
    exit 0
  fi
done

echo 'Could not find a system CA certificate bundle.' >&2
exit 1
