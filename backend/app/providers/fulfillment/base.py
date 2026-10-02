from dataclasses import dataclass, field
from decimal import Decimal
from typing import Protocol

from app.core.enums import ProviderCode
from app.models import Order


@dataclass
class ProviderPrices:
    premium_ton: dict[int, Decimal] = field(default_factory=dict)
    star_unit_ton: Decimal | None = None


@dataclass
class RecipientInfo:
    found: bool
    name: str | None = None
    photo_url: str | None = None
    can_receive: bool = True
    reason: str | None = None
    token: str | None = None  # provider-specific recipient handle


@dataclass
class DeliveryResult:
    provider_ref: str
    cost_amount: Decimal
    cost_currency: str  # "TON" | "XTR"
    network_fee_ton: Decimal = Decimal(0)


class FulfillmentProvider(Protocol):
    code: ProviderCode

    async def supports(self, order: Order) -> bool: ...

    async def is_available(self) -> bool: ...

    async def get_prices(self) -> ProviderPrices: ...

    async def resolve_recipient(self, username: str, product: str = "premium", months: int = 3) -> RecipientInfo: ...

    async def deliver(self, order: Order) -> DeliveryResult:
        """Raise ProviderUnavailable (safe to retry), RecipientInvalid (permanent) or
        ProviderUncertain (money may have moved — needs human review)."""
        ...
