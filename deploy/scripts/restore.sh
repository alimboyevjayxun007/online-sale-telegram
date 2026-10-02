#!/usr/bin/env bash
# Restore a dump into a database. Usage: restore.sh <dump|dump.age> [target_database_url]
# Without a target it restores into a scratch database "premium_restore_test" to PROVE the backup works.
set -euo pipefail
file="${1:?usage: restore.sh <dump> [target_url]}"
target="${2:-}"
work="$file"
if [[ "$file" == *.age ]]; then
  work="$(mktemp)"; age -d -i "${AGE_IDENTITY:?set AGE_IDENTITY to your age private key file}" -o "$work" "$file"
fi
if [[ -z "$target" ]]; then
  admin="${DATABASE_URL/postgresql+asyncpg/postgresql}"
  dropdb --if-exists --maintenance-db="$admin" premium_restore_test || true
  createdb --maintenance-db="$admin" premium_restore_test
  target="${admin%/*}/premium_restore_test"
fi
pg_restore --no-owner --clean --if-exists --dbname="$target" "$work"
echo "restored into $target"
[[ "$work" != "$file" ]] && rm -f "$work"
exit 0
