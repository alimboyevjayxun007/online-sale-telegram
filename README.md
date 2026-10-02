# Soft-tg-Market — Telegram Premium & Stars bot

Foydalanuvchilar **Telegram Premium** (3/6/12 oy) va **⭐ Stars**'ni eng arzon narxda TON, Stars yoki ichki balans bilan sotib oladi.
Egasi (owner) butun biznesni botning o'zidan (BotFather uslubida) **va** Mini App'dan boshqaradi.

- **Backend:** Python 3.13 · FastAPI · aiogram 3 · SQLAlchemy 2 (async) · PostgreSQL · Redis
- **Mini App:** Next.js 16 · React 19 · Tailwind 4 · TON Connect · Recharts
- **Deploy:** Docker'siz — systemd + Nginx (`deploy/`)
- To'liq reja, arxitektura va diagrammalar: [`ISH_REJASI.md`](ISH_REJASI.md)

## Mahalliy ishga tushirish (ishlab chiqish)

Kerak: Python 3.13 + [uv](https://docs.astral.sh/uv/), Node 22+ + pnpm, PostgreSQL 16+, Redis 7.

```bash
cd backend
cp .env.example .env        # BOT_TOKEN (TEST bot), OWNER_TELEGRAM_ID, ENCRYPTION_KEY ... ni to'ldiring
uv sync
uv run python -m app.cli gen-keys          # APP_SECRET_KEY / ENCRYPTION_KEY / WEBHOOK_SECRET
createdb premium && createdb premium_test  # (role: premium/premium yoki .env dagi DATABASE_URL)
make migrate && make seed                  # jadval + demo kurslar/narxlar (faqat dev!)

# 4 ta terminal (yoki 4 ta jarayon):
make dev-api      # http://localhost:8000  (/api/docs)
make dev-worker   # TON kuzatuvchi, yetkazish, xabarlar, statistika ...  (DEV_MOCK_PROVIDER=true bo'lsa Fragment o'rniga mock)
make dev-bot      # botni long-polling bilan ishga tushiradi (domen kerak emas)
make dev-web      # http://localhost:3000  (Mini App)
```

Mini App'ni Telegram'siz brauzerda ochish uchun: `uv run python -m app.cli dev-mock` chiqargan satrni brauzer konsolida
`localStorage.setItem("devInitData", "<satr>")` bilan saqlang (faqat `NODE_ENV!=production`).

```bash
make test    # 76 ta backend test (haqiqiy PostgreSQL + Redis kerak: premium_test bazasi)
make lint    # ruff + mypy + eslint + tsc
make e2e     # brauzer E2E (Playwright), api+worker+web ishlab turganda
```

## Production (Ubuntu 24.04, Dockersiz)

1. DNS: `A` yozuv → server IP. 2. `deploy/scripts/bootstrap_server.sh` (root) — PostgreSQL, Redis, Nginx, TLS, systemd.
3. `/etc/premium/backend.env` ni to'ldiring (`deploy/env/backend.env.example`) — `BOT_TOKEN`ni **faqat serverda** kiriting.
4. `deploy/scripts/deploy.sh` — migratsiya, webhook, build, restart.
5. `python -m app.cli wallet generate` — hot wallet **serverda** yaratiladi; 24 so'zni qog'ozga yozing.
6. BotFather: Mini App URL = `https://<domen>/`, Menu Button avtomatik o'rnatiladi.

Batafsil: `ISH_REJASI.md` §16 va §22.

## Muhim xavfsizlik qoidalari

- Bot tokeni, hamyon seed iborasi, Fragment cookie'lari hech qachon git/chatga tushmaydi (`.env`, shifrlangan fayl, admin panel).
- Pul faqat `.env` dagi `ADMIN_TON_ADDRESS` ga yechiladi; yechish faqat `owner` roli uchun.
- `DEV_MOCK_PROVIDER` production'da yoqilsa ilova ishga tushmaydi.
