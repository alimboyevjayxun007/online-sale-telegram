.PHONY: lint test dev-api dev-web migrate
lint:
	cd backend && uv run ruff check . && uv run mypy app
	cd webapp && pnpm lint && pnpm exec tsc --noEmit
test:
	cd backend && uv run pytest -q
dev-api:
	cd backend && uv run uvicorn app.main:app --reload --port 8000
dev-web:
	cd webapp && pnpm dev
migrate:
	cd backend && uv run alembic upgrade head
