from decimal import Decimal
from typing import Protocol

import httpx

from app.core.config import get_settings
from app.core.money import D


class RateSource(Protocol):
    name: str

    async def fetch(self, pair: str) -> Decimal: ...


class TonApiRates:
    name = "tonapi"

    async def fetch(self, pair: str) -> Decimal:
        if pair != "TON_USD":
            raise ValueError(pair)
        headers = {}
        key = get_settings().tonapi_key.get_secret_value()
        if key:
            headers["Authorization"] = f"Bearer {key}"
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                "https://tonapi.io/v2/rates", params={"tokens": "ton", "currencies": "usd"}, headers=headers
            )
            r.raise_for_status()
            return D(r.json()["rates"]["TON"]["prices"]["USD"])


class CoinGeckoRates:
    name = "coingecko"

    async def fetch(self, pair: str) -> Decimal:
        if pair != "TON_USD":
            raise ValueError(pair)
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "the-open-network", "vs_currencies": "usd"},
            )
            r.raise_for_status()
            return D(r.json()["the-open-network"]["usd"])


class CbuRates:
    name = "cbu"

    async def fetch(self, pair: str) -> Decimal:
        if pair != "USD_UZS":
            raise ValueError(pair)
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/USD/")
            r.raise_for_status()
            return D(r.json()[0]["Rate"])
