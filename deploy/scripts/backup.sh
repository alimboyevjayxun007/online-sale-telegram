#!/usr/bin/env bash
# Daily PostgreSQL backup: custom-format dump, optional age encryption, retention, optional Telegram delivery.
set -euo pipefail
BACKUP_DIR="${BACKUP_DIR:-/var/backups/premium}"
KEEP_DAYS="${BACKUP_KEEP_DAYS:-14}"
DB_URL="${DATABASE_URL:?DATABASE_URL is required}"
PG_URL="${DB_URL/postgresql+asyncpg/postgresql}"          # pg_dump wants a plain libpq URL
mkdir -p "$BACKUP_DIR"
stamp="$(date +%Y%m%d-%H%M%S)"
out="$BACKUP_DIR/premium-$stamp.dump"
pg_dump --format=custom --no-owner --dbname="$PG_URL" --file="$out"
if [[ -n "${BACKUP_AGE_RECIPIENT:-}" ]]; then
  age -r "$BACKUP_AGE_RECIPIENT" -o "$out.age" "$out" && rm -f "$out"
  out="$out.age"
fi
chmod 600 "$out"
find "$BACKUP_DIR" -name 'premium-*.dump*' -mtime +"$KEEP_DAYS" -delete
size=$(stat -c %s "$out")
if [[ -n "${BOT_TOKEN:-}" && -n "${OWNER_TELEGRAM_ID:-}" && "$size" -lt 49000000 && -n "${BACKUP_AGE_RECIPIENT:-}" ]]; then
  # only encrypted dumps are ever sent over Telegram
  curl -fsS -m 120 -F "chat_id=$OWNER_TELEGRAM_ID" -F "document=@$out" -F "caption=🗄 backup $stamp" \
    "https://api.telegram.org/bot${BOT_TOKEN}/sendDocument" >/dev/null || echo "telegram delivery failed (backup kept locally)" >&2
fi
echo "backup ok: $out ($size bytes)"
