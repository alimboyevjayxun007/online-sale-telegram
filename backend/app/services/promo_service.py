from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ProductScope, ProductType, PromoType
from app.core.errors import PromoInvalid
from app.core.money import quantize
from app.core.timeutil import now_utc
from app.models import PromoCode, PromoRedemption


class PromoService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def validate(
        self, code: str, user_id: int, product: ProductType, price_usd: Decimal, lock: bool = False
    ) -> PromoCode:
        stmt = select(PromoCode).where(func.upper(PromoCode.code) == code.strip().upper())
        if lock:
            stmt = stmt.with_for_update()
        promo = await self.session.scalar(stmt)
        now = now_utc()
        if promo is None or not promo.is_active:
            raise PromoInvalid("not_found")
        if promo.valid_from and promo.valid_from > now:
            raise PromoInvalid("not_started")
        if promo.valid_to and promo.valid_to < now:
            raise PromoInvalid("expired")
        if promo.max_uses is not None and promo.used_count >= promo.max_uses:
            raise PromoInvalid("limit_reached")
        if promo.applies_to != ProductScope.ALL and promo.applies_to.value != product.value:
            raise PromoInvalid("wrong_product")
        if promo.min_order_usd is not None and price_usd < promo.min_order_usd:
            raise PromoInvalid("min_order", min_order_usd=str(promo.min_order_usd))
        used = await self.session.scalar(
            select(func.count())
            .select_from(PromoRedemption)
            .where(PromoRedemption.promo_id == promo.id, PromoRedemption.user_id == user_id)
        )
        if (used or 0) >= promo.per_user_limit:
            raise PromoInvalid("already_used")
        return promo

    @staticmethod
    def discount_for(promo: PromoCode, price_usd: Decimal) -> Decimal:
        if promo.type == PromoType.PERCENT:
            d = price_usd * promo.value / 100
        else:
            d = promo.value
        return quantize(min(d, price_usd))

    async def redeem(self, promo: PromoCode, user_id: int, order_id: int, discount: Decimal) -> None:
        promo.used_count += 1
        self.session.add(PromoRedemption(promo_id=promo.id, user_id=user_id, order_id=order_id, discount_usd=discount))
