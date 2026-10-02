#!/usr/bin/env bash
# One-time server preparation for Ubuntu 24.04 (run as root). No Docker: systemd + Nginx + PostgreSQL + Redis.
# Usage: sudo DOMAIN=premium.example.uz EMAIL=you@mail.com REPO=https://github.com/<owner>/online-sale-telegram.git ./bootstrap_server.sh
set -euo pipefail
: "${DOMAIN:?set DOMAIN}"; : "${EMAIL:?set EMAIL}"; : "${REPO:?set REPO}"

apt-get update && DEBIAN_FRONTEND=noninteractive apt-get -y upgrade
DEBIAN_FRONTEND=noninteractive apt-get -y install git curl build-essential ufw fail2ban unattended-upgrades nginx certbot python3-certbot-nginx age redis-server postgresql-common

id premium >/dev/null 2>&1 || adduser --system --group --home /opt/premium premium
mkdir -p /etc/premium /var/lib/premium /var/backups/premium
chown premium:premium /var/lib/premium /var/backups/premium; chmod 700 /etc/premium; chown premium:premium /etc/premium

ufw allow OpenSSH; ufw allow 'Nginx Full'; ufw --force enable

# PostgreSQL (PGDG, current major) + role/database with a generated password
/usr/share/postgresql-common/pgdg/apt.postgresql.org.sh -y
DEBIAN_FRONTEND=noninteractive apt-get -y install postgresql
PGPASS="$(openssl rand -hex 16)"; REDISPASS="$(openssl rand -hex 16)"
sudo -u postgres psql -c "CREATE ROLE premium LOGIN PASSWORD '$PGPASS';" || sudo -u postgres psql -c "ALTER ROLE premium PASSWORD '$PGPASS';"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='premium'" | grep -q 1 || sudo -u postgres createdb -O premium premium
# Redis: localhost only + password
sed -i "s/^# *requirepass .*/requirepass $REDISPASS/; s/^bind .*/bind 127.0.0.1 -::1/" /etc/redis/redis.conf
systemctl restart redis-server

# toolchains
curl -LsSf https://astral.sh/uv/install.sh | sudo -u premium env UV_INSTALL_DIR=/opt/premium/.local/bin sh
curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && apt-get -y install nodejs && corepack enable

# code
[[ -d /opt/premium/app ]] || sudo -u premium git clone "$REPO" /opt/premium/app
cp -n /opt/premium/app/deploy/env/backend.env.example /etc/premium/backend.env
cp -n /opt/premium/app/deploy/env/webapp.env.example /etc/premium/webapp.env
sed -i "s#CHANGE_ME@127.0.0.1:5432#$PGPASS@127.0.0.1:5432#; s#:CHANGE_ME@127.0.0.1:6379#:$REDISPASS@127.0.0.1:6379#; s#premium.example.uz#$DOMAIN#g" /etc/premium/backend.env /etc/premium/webapp.env
chown premium:premium /etc/premium/*.env; chmod 600 /etc/premium/*.env

# units + nginx
cp /opt/premium/app/deploy/systemd/*.service /opt/premium/app/deploy/systemd/*.timer /etc/systemd/system/
sed "s/premium.example.uz/$DOMAIN/g" /opt/premium/app/deploy/nginx/premium.conf > /etc/nginx/sites-available/premium.conf
# first obtain the certificate with a plain :80 site, then switch to the full config
cat > /etc/nginx/sites-enabled/premium.conf <<NGX
server { listen 80; server_name $DOMAIN; location / { return 200 'ok'; } }
NGX
rm -f /etc/nginx/sites-enabled/default; nginx -t && systemctl reload nginx
certbot certonly --nginx -d "$DOMAIN" -m "$EMAIL" --agree-tos -n
ln -sf /etc/nginx/sites-available/premium.conf /etc/nginx/sites-enabled/premium.conf
nginx -t && systemctl reload nginx

systemctl daemon-reload
echo
echo "NEXT STEPS (as root):"
echo "  1. nano /etc/premium/backend.env     → fill BOT_TOKEN, BOT_USERNAME, ADMIN_TON_ADDRESS, TONAPI_KEY, LOG_CHAT_ID, and run"
echo "     sudo -u premium /opt/premium/app/backend/.venv/bin/python -m app.cli gen-keys   (after first deploy) for APP_SECRET_KEY/ENCRYPTION_KEY/WEBHOOK_SECRET"
echo "  2. nano /etc/premium/webapp.env      → NEXT_PUBLIC_BOT_USERNAME"
echo "  3. sudo -u premium /opt/premium/app/deploy/scripts/deploy.sh"
echo "  4. sudo -u premium bash -c 'set -a; source /etc/premium/backend.env; cd /opt/premium/app/backend && .venv/bin/python -m app.cli wallet generate'   ← WRITE THE 24 WORDS ON PAPER"
echo "  5. systemctl enable --now premium-api premium-worker premium-web premium-backup.timer"
