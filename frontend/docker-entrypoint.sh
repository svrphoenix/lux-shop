#!/bin/sh

set -eu

lock_hash="$(sha256sum package-lock.json | cut -d ' ' -f 1)"
installed_hash_file="node_modules/.package-lock.sha256"

if [ ! -f "$installed_hash_file" ] || [ "$(cat "$installed_hash_file")" != "$lock_hash" ]; then
  npm ci
  printf '%s\n' "$lock_hash" > "$installed_hash_file"
fi

exec npm run dev -- --hostname 0.0.0.0
