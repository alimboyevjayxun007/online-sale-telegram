from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.api.runtime import set_runtime
from app.api.webhooks import router as webhook_router
from app.core.config import get_settings
from app.core.db import dispose_engine
from app.core.errors import AppError
from app.core.logging import setup_logging
from app.core.redis import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    settings = get_settings()
    if settings.is_production:
        missing = settings.validate_for_production()
        if missing:
            raise RuntimeError(f"Missing required settings: {', '.join(missing)}")
    from app.bot.setup import build_runtime, create_dispatcher

    rt = build_runtime()
    set_runtime(rt)
    app.state.bot = rt.bot
    app.state.dp = create_dispatcher(rt) if rt.bot is not None else None
    yield
    if rt.bot is not None:
        await rt.bot.session.close()
    await close_redis()
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Soft-tg-Market API",
        lifespan=lifespan,
        docs_url=None if settings.is_production else "/api/docs",
        openapi_url=None if settings.is_production else "/api/openapi.json",
    )

    @app.exception_handler(AppError)
    async def app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
        )

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router)
    app.include_router(webhook_router)
    return app


app = create_app()
