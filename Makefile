.PHONY: lint test dev-api dev-bot dev-worker dev-web migrate seed e2e
lint:
	cd backend && uv run ruff check . && uv run mypy app
	cd webapp && pnpm lint && pnpm exec tsc --noEmit
test:
	cd backend && uv run pytest -q
dev-api:
	cd backend && uv run uvicorn app.main:app --reload --port 8000
dev-bot:            # long polling: no domain/HTTPS needed
	cd backend && uv run python -m app.cli bot poll
dev-worker:
	cd backend && uv run python -m app.workers.runner
dev-web:
	cd webapp && pnpm dev
migrate:
	cd backend && uv run alembic upgrade head
seed:               # DEVELOPMENT ONLY: fake rates, plan costs, placeholder wallet
	cd backend && uv run python -m app.cli db seed-owner && uv run python -m app.cli db dev-seed
e2e:                # needs api + worker (DEV_MOCK_PROVIDER=true) + web running; see webapp/e2e/*.mjs header
	cd webapp && pnpm e2e:ton && pnpm e2e:admin
