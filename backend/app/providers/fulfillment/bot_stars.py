from decimal import Decimal

import structlog

from app.core.enums import ProductType, ProviderCode
from app.core.errors import ProviderUnavailable, RecipientInvalid
from app.models import Order
from app.providers.fulfillment.base import DeliveryResult, ProviderPrices, RecipientInfo
from app.providers.fulfillment.gateway import StarsGateway

log = structlog.get_logger()
# Bot API giftPremiumSubscription: only these (months -> stars) pairs are accepted by Telegram
GIFT_STARS = {3: 1000, 6: 1500, 12: 2500}


class BotStarsProvider:
    """Official route: bot pays with its own Stars balance (giftPremiumSubscription). Needs a user_id."""

    code = ProviderCode.BOT_STARS

    def __init__(self, gateway: StarsGateway) -> None:
        self.gw = gateway

    async def supports(self, order: Order) -> bool:
        return (
            order.product_type == ProductType.PREMIUM
            and order.plan_months in GIFT_STARS
            and bool(order.recipient_user_id)
        )

    async def is_available(self) -> bool:
        return True

    async def get_prices(self) -> ProviderPrices:
        return ProviderPrices()

    async def resolve_recipient(self, username: str, product: str = "premium", months: int = 3) -> RecipientInfo:
        return RecipientInfo(True, name=username)

    async def deliver(self, order: Order) -> DeliveryResult:
        months = order.plan_months or 0
        stars = GIFT_STARS[months]
        assert order.recipient_user_id is not None
        try:
            if await self.gw.star_balance() < stars:
                raise ProviderUnavailable("bot stars balance too low")
            await self.gw.gift_premium(order.recipient_user_id, months, stars)
        except (ProviderUnavailable, RecipientInvalid):
            raise
        except Exception as exc:  # noqa: BLE001 - aiogram errors are classified by message
            msg = str(exc).lower()
            if "user_not_found" in msg or "bad request" in msg:
                raise RecipientInvalid(str(exc)) from exc
            raise ProviderUnavailable(str(exc)) from exc
        return DeliveryResult(f"gift-{order.public_id}", Decimal(stars), "XTR")
