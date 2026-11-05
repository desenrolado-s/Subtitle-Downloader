#!/usr/bin/env bash
# Print the next release version using the project's single-digit rollover:
# 2.0.8 -> 2.0.9, 2.0.9 -> 2.1.0, 2.9.9 -> 3.0.0.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ "$#" -gt 0 ]; then
  latest=$1
else
  latest=$(git tag --list 'v*' | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -n 1 || true)
fi
latest=${latest#v}

if [ -z "$latest" ]; then
  printf '0.0.1\n'
  exit 0
fi

IFS=. read -r major minor patch <<< "$latest"
major=${major:-0}
minor=${minor:-0}
patch=${patch:-0}

patch=$((patch + 1))
if [ "$patch" -gt 9 ]; then
  patch=0
  minor=$((minor + 1))
fi
if [ "$minor" -gt 9 ]; then
  minor=0
  major=$((major + 1))
fi

printf '%s.%s.%s\n' "$major" "$minor" "$patch"
