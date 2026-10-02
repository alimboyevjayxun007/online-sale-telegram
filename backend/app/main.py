from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    settings = get_settings()
    if settings.is_production:
        missing = settings.validate_for_production()
        if missing:
            raise RuntimeError(f"Missing required settings: {', '.join(missing)}")
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Soft-tg-Market API",
        lifespan=lifespan,
        docs_url=None if settings.is_production else "/api/docs",
        openapi_url=None if settings.is_production else "/api/openapi.json",
    )

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
