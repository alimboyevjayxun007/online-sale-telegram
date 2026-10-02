#!/usr/bin/env bash
# Update the running server to the latest origin/main. Run as the `premium` user:  sudo -u premium /opt/premium/app/deploy/scripts/deploy.sh
set -euo pipefail
cd /opt/premium/app
git fetch origin "${BRANCH:-main}"
git reset --hard "origin/${BRANCH:-main}"

echo "→ backend"
cd backend
uv sync --frozen --no-dev
set -a; source /etc/premium/backend.env; set +a
uv run alembic upgrade head
uv run python -m app.cli db seed-owner
uv run python -m app.cli bot set-webhook          # webhook + commands + menu button + descriptions
cd ..

echo "→ webapp"
cd webapp
set -a; source /etc/premium/webapp.env; set +a
pnpm install --frozen-lockfile
pnpm build
mkdir -p .next/standalone/.next
cp -r public .next/standalone/
cp -r .next/static .next/standalone/.next/
cd ..

echo "→ restart"
sudo systemctl restart premium-api premium-worker premium-web
sleep 3
curl -fsS "${PUBLIC_BASE_URL:-http://127.0.0.1:8000}/api/health" && echo
echo "deployed $(git rev-parse --short HEAD)"
