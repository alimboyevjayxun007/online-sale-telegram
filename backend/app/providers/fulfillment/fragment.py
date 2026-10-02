"""Fragment.com adapters.

Fragment has no official public API. ``FragmentWebClient`` talks to the same JSON endpoint the website uses
(POST /api?hash=...) with the owner's session cookies, then the TON transfer is signed locally by the hot wallet.
The request/response shapes below follow the website's behaviour and MUST be verified against the live site
(see ISH_REJASI.md §2.5) before going to production — they are covered by respx-based tests only.
"""

import json
import re
from decimal import Decimal
from typing import Any

import httpx
import structlog

from app.core.enums import ProductType, ProviderCode
from app.core.errors import ProviderUnavailable, ProviderUncertain, RecipientInvalid
from app.core.money import D
from app.models import Order
from app.providers.fulfillment.base import DeliveryResult, ProviderPrices, RecipientInfo
from app.providers.ton.wallet import TonSigner

log = structlog.get_logger()
BASE = "https://fragment.com"
DEVICE = {
    "platform": "web",
    "appName": "tonkeeper",
    "appVersion": "3.0.0",
    "maxProtocolVersion": 2,
    "features": ["SendTransaction", {"name": "SendTransaction", "maxMessages": 4}],
}


class FragmentWebClient:
    def __init__(self, cookies: dict[str, str], account: dict[str, str]) -> None:
        self.cookies, self.account = cookies, account
        self._hash: str | None = None

    async def _api_hash(self, c: httpx.AsyncClient) -> str:
        if self._hash is None:
            r = await c.get(f"{BASE}/premium/gift")
            m = re.search(r"api\?hash=([0-9a-f]+)", r.text)
            if not m:
                raise ProviderUnavailable("fragment: api hash not found (cookies expired?)")
            self._hash = m.group(1)
        return self._hash

    async def call(self, method: str, **data: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30, cookies=self.cookies, headers={"User-Agent": "Mozilla/5.0"}) as c:
            h = await self._api_hash(c)
            r = await c.post(f"{BASE}/api?hash={h}", data={"method": method, **data})
        if r.status_code >= 500:
            raise ProviderUnavailable(f"fragment http {r.status_code}")
        try:
            return dict(r.json())
        except ValueError as exc:
            raise ProviderUnavailable("fragment: bad json") from exc

    async def search_recipient(self, username: str, product: str, months: int = 3) -> dict[str, Any]:
        if product == "premium":
            return await self.call("searchPremiumGiftRecipient", query=username, months=str(months))
        return await self.call("searchStarsRecipient", query=username)

    async def init_purchase(self, recipient: str, product: str, qty: int) -> dict[str, Any]:
        if product == "premium":
            return await self.call("initGiftPremiumRequest", recipient=recipient, months=str(qty))
        return await self.call("initBuyStarsRequest", recipient=recipient, quantity=str(qty))

    async def get_transaction(self, req_id: str, product: str) -> dict[str, Any]:
        method = "getGiftPremiumLink" if product == "premium" else "getBuyStarsLink"
        return await self.call(
            method,
            transaction="1",
            id=req_id,
            show_sender="0",
            account=json.dumps(self.account),
            device=json.dumps(DEVICE),
        )


class FragmentDirectProvider:
    code = ProviderCode.FRAGMENT_DIRECT

    def __init__(self, client: FragmentWebClient | None, signer: TonSigner | None) -> None:
        self.client, self.signer = client, signer

    async def supports(self, order: Order) -> bool:
        return bool(order.recipient_username) and (
            order.plan_months in (3, 6, 12) or order.product_type == ProductType.STARS
        )

    async def is_available(self) -> bool:
        return self.client is not None and self.signer is not None

    async def get_prices(self) -> ProviderPrices:
        return ProviderPrices()  # filled from the live page once verified; admin can set cost manually meanwhile

    async def resolve_recipient(self, username: str, product: str = "premium", months: int = 3) -> RecipientInfo:
        if self.client is None:
            raise ProviderUnavailable("fragment not configured")
        data = await self.client.search_recipient(username.lstrip("@"), product, months)
        found = data.get("found")
        if not found:
            return RecipientInfo(False, reason=str(data.get("error") or "not_found"))
        return RecipientInfo(True, name=found.get("name"), photo_url=found.get("photo"), token=found.get("recipient"))

    async def deliver(self, order: Order) -> DeliveryResult:
        if self.client is None or self.signer is None:
            raise ProviderUnavailable("fragment not configured")
        product = order.product_type.value
        qty = order.plan_months if order.product_type == ProductType.PREMIUM else order.stars_amount
        assert qty and order.recipient_username
        rec = await self.client.search_recipient(
            order.recipient_username.lstrip("@"), product, qty if product == "premium" else 3
        )
        found = rec.get("found")
        if not found:
            raise RecipientInvalid(str(rec.get("error") or "recipient not found"))
        init = await self.client.init_purchase(found["recipient"], product, qty)
        req_id = init.get("req_id")
        if not req_id:
            raise RecipientInvalid(str(init.get("error") or "init failed"))
        tx = await self.client.get_transaction(req_id, product)
        messages = (tx.get("transaction") or {}).get("messages") or []
        if not messages:
            raise ProviderUnavailable(str(tx.get("error") or "no transaction"))
        msg = messages[0]
        amount_nano = int(msg["amount"])
        # From here on money may leave the wallet: any failure is UNCERTAIN, never auto-retried.
        try:
            tx_hash = await self.signer.send(msg["address"], amount_nano, body_b64=msg.get("payload"))
        except Exception as exc:  # noqa: BLE001
            raise ProviderUncertain(f"send failed: {exc}") from exc
        return DeliveryResult(tx_hash, D(amount_nano) / Decimal(10**9), "TON")


class FragmentApiProvider:
    """Third-party REST vendor (fallback). Not wired to a vendor yet — reports itself unavailable."""

    code = ProviderCode.FRAGMENT_API

    async def supports(self, order: Order) -> bool:
        return False

    async def is_available(self) -> bool:
        return False

    async def get_prices(self) -> ProviderPrices:
        return ProviderPrices()

    async def resolve_recipient(self, username: str, product: str = "premium", months: int = 3) -> RecipientInfo:
        raise ProviderUnavailable("fragment_api not configured")

    async def deliver(self, order: Order) -> DeliveryResult:
        raise ProviderUnavailable("fragment_api not configured")
