from decimal import Decimal

from app.core.enums import ProductType, ProviderCode
from app.core.errors import ProviderUnavailable, ProviderUncertain, RecipientInvalid
from app.models import Order
from app.providers.fulfillment.base import DeliveryResult, ProviderPrices, RecipientInfo


class MockProvider:
    """Deterministic provider for development and tests."""

    code = ProviderCode.MOCK

    def __init__(self, mode: str = "ok") -> None:
        self.mode = mode  # ok | unavailable | invalid | uncertain
        self.delivered: list[str] = []
        self.calls = 0

    async def supports(self, order: Order) -> bool:
        return True

    async def is_available(self) -> bool:
        return self.mode != "down"

    async def get_prices(self) -> ProviderPrices:
        return ProviderPrices(
            premium_ton={3: Decimal("4.00"), 6: Decimal("5.33"), 12: Decimal("9.66")},
            star_unit_ton=Decimal("0.005"),
        )

    async def resolve_recipient(self, username: str, product: str = "premium", months: int = 3) -> RecipientInfo:
        if username.lower().startswith("nouser"):
            return RecipientInfo(False, reason="not_found")
        if username.lower().startswith("nopremium"):
            return RecipientInfo(True, name=username, can_receive=False, reason="already_premium")
        return RecipientInfo(True, name=f"Mock {username}", token=username)

    async def deliver(self, order: Order) -> DeliveryResult:
        self.calls += 1
        if self.mode == "unavailable":
            raise ProviderUnavailable("mock down")
        if self.mode == "invalid":
            raise RecipientInvalid("mock invalid")
        if self.mode == "uncertain":
            raise ProviderUncertain("mock uncertain")
        self.delivered.append(order.public_id)
        if order.product_type == ProductType.PREMIUM:
            return DeliveryResult(f"mock-{order.public_id}", Decimal("4.05"), "TON")
        return DeliveryResult(f"mock-{order.public_id}", Decimal(order.stars_amount or 0) * Decimal("0.005"), "TON")
