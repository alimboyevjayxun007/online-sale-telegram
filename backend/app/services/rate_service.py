from decimal import Decimal

import structlog
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.money import D
from app.models import ExchangeRate
from app.providers.rates.sources import CbuRates, CoinGeckoRates, RateSource, TonApiRates

log = structlog.get_logger()
SOURCES: dict[str, list[RateSource]] = {
    "TON_USD": [TonApiRates(), CoinGeckoRates()],
    "USD_UZS": [CbuRates()],
}
FALLBACK = {"TON_USD": Decimal("3"), "USD_UZS": Decimal("12800")}


class RateService:
    def __init__(self, session: AsyncSession, redis: Redis | None) -> None:
        self.session = session
        self.redis = redis

    async def _get(self, pair: str) -> Decimal:
        if self.redis is not None:
            cached = await self.redis.get(f"rate:{pair}")
            if cached:
                return D(cached)
        row = await self.session.scalar(
            select(ExchangeRate).where(ExchangeRate.pair == pair).order_by(ExchangeRate.fetched_at.desc()).limit(1)
        )
        if row is not None:
            return row.rate
        log.warning("rate_fallback_used", pair=pair)
        return FALLBACK[pair]

    async def ton_usd(self) -> Decimal:
        return await self._get("TON_USD")

    async def usd_uzs(self) -> Decimal:
        return await self._get("USD_UZS")

    async def set_rate(self, pair: str, rate: Decimal, source: str) -> None:
        self.session.add(ExchangeRate(pair=pair, rate=rate, source=source))
        if self.redis is not None:
            await self.redis.set(f"rate:{pair}", str(rate), ex=3600)

    async def refresh(self, pairs: list[str] | None = None) -> dict[str, Decimal]:
        """Fetch fresh rates; try each source in order, keep the old value if all fail."""
        out: dict[str, Decimal] = {}
        for pair in pairs or list(SOURCES):
            for src in SOURCES[pair]:
                try:
                    rate = await src.fetch(pair)
                except Exception as exc:  # noqa: BLE001 - any failure → try next source
                    log.warning("rate_source_failed", pair=pair, source=src.name, error=str(exc))
                    continue
                if rate > 0:
                    await self.set_rate(pair, rate, src.name)
                    out[pair] = rate
                    break
        return out
