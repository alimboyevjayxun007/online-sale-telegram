import asyncio
import os

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://premium:premium@127.0.0.1:5432/premium_test"
)
os.environ["REDIS_URL"] = os.environ.get("TEST_REDIS_URL", "redis://127.0.0.1:6379/1")
os.environ["BOT_TOKEN"] = "123456:TESTTOKENTESTTOKENTESTTOKENTESTTOKEN"
os.environ["OWNER_TELEGRAM_ID"] = "1000"
os.environ["ENCRYPTION_KEY"] = "yQ0m3m1h0m8V8p5m6F3K8e6k1Zf2o9fX3m5v7b9c1d4="
os.environ["APP_SECRET_KEY"] = "test-secret"
os.environ["BOT_USERNAME"] = "TestBot"
os.environ["THROTTLE_MS"] = "0"
os.environ["ADMIN_TON_ADDRESS"] = "UQAdminAddress"

import pytest  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app import models  # noqa: E402,F401
from app.core.db import Base, dispose_engine, get_engine, session_maker  # noqa: E402
from app.core.redis import close_redis, get_redis  # noqa: E402
from app.services import settings_service  # noqa: E402


async def _create_schema() -> None:
    eng = get_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        # drop_all leaves the PostgreSQL enum types behind; recreate them from the current models
        enum_names = {
            c.type.name for tb in Base.metadata.tables.values() for c in tb.columns if hasattr(c.type, "enums")
        }
        for name in sorted(n for n in enum_names if n):
            await conn.execute(text(f'DROP TYPE IF EXISTS "{name}" CASCADE'))
        await conn.run_sync(Base.metadata.create_all)
    await dispose_engine()


@pytest.fixture(scope="session", autouse=True)
def schema() -> None:
    asyncio.run(_create_schema())


@pytest.fixture(autouse=True)
async def clean():
    settings_service.clear_cache()
    eng = get_engine()
    names = ",".join(f'"{t}"' for t in Base.metadata.tables)
    async with eng.begin() as conn:
        await conn.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))
    await get_redis().flushdb()
    yield
    await close_redis()
    await dispose_engine()


@pytest.fixture
async def session():
    async with session_maker()() as s:
        yield s
        await s.commit()
