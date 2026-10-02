from dataclasses import dataclass, field
from decimal import Decimal

from app.core.enums import PaymentMethod
from app.core.errors import PlanUnavailable, ValidationFailed
from app.core.money import D, ceil_places, quantize, round_to, round_up
from app.models import PremiumPlan, PromoCode
from app.services.promo_service import PromoService
from app.services.rate_service import RateService
from app.services.settings_service import SettingsService


@dataclass
class Quote:
    price_usd: Decimal
    price_ton: Decimal
    price_xtr: int
    price_uzs: int
    cost_usd: Decimal
    discount_usd: Decimal = Decimal(0)
    min_price_usd: Decimal = Decimal(0)
    ton_usd: Decimal = Decimal(0)
    usd_uzs: Decimal = Decimal(0)
    reference_price_usd: Decimal | None = None
    extra: dict[str, object] = field(default_factory=dict)

    def amount_for(self, method: PaymentMethod) -> tuple[Decimal, str]:
        if method == PaymentMethod.TON:
            return self.price_ton, "TON"
        if method == PaymentMethod.STARS:
            return Decimal(self.price_xtr), "XTR"
        return self.price_usd, "USD"


class PricingService:
    """All prices are computed server-side (see ISH_REJASI.md §3.3-3.5)."""

    def __init__(self, rates: RateService, settings: SettingsService, promo: PromoService | None = None) -> None:
        self.rates, self.settings, self.promo = rates, settings, promo

    async def _common(self) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal]:
        s = self.settings
        return (
            await self.rates.ton_usd(),
            await self.rates.usd_uzs(),
            D(await s.get("pricing.min_margin_percent")),
            D(await s.get("pricing.round_step_usd")),
            D(await s.get("pricing.star_usd_rate")),
        )

    def _finish(
        self, price: Decimal, cost: Decimal, min_price: Decimal, ton_usd: Decimal, usd_uzs: Decimal, xtr: int
    ) -> Quote:
        return Quote(
            price_usd=quantize(price),
            price_ton=ceil_places(price / ton_usd, 2),
            price_xtr=xtr,
            price_uzs=round_to(price * usd_uzs, 1000),
            cost_usd=quantize(cost),
            min_price_usd=quantize(min_price),
            ton_usd=ton_usd,
            usd_uzs=usd_uzs,
        )

    async def quote_premium(self, plan: PremiumPlan, promo: PromoCode | None = None) -> Quote:
        if not plan.is_enabled or not plan.provider_supported:
            raise PlanUnavailable("plan disabled")
        ton_usd, usd_uzs, margin, step, star_rate = await self._common()
        fee = D(await self.settings.get("pricing.network_fee_ton"))
        if plan.cost_ton is not None:
            cost = (plan.cost_ton + fee) * ton_usd
        else:
            # no live price yet: fall back to the USD list price, converted at the current TON rate
            fallback = (await self.settings.get("pricing.fallback_cost_usd") or {}).get(str(plan.months))
            if fallback is not None:
                cost = D(fallback) + fee * ton_usd
            elif plan.fixed_price_usd is not None:
                cost = Decimal(0)
            else:
                raise PlanUnavailable("cost unknown")
        min_price = cost * (1 + margin / 100)
        if plan.fixed_price_usd is not None:
            raw = plan.fixed_price_usd
        else:
            raw = cost * (1 + plan.markup_percent / 100) + plan.fixed_markup_usd
        price = round_up(max(raw, min_price), step)
        xtr = plan.price_stars or int(ceil_places(price / star_rate, 0))
        q = self._finish(price, cost, min_price, ton_usd, usd_uzs, xtr)
        q.reference_price_usd = plan.reference_price_usd
        return self._apply_promo(q, promo, step)

    async def quote_stars(self, amount: int, promo: PromoCode | None = None) -> Quote:
        max_amount = int(await self.settings.get("pricing.stars.max_amount"))
        if amount < 50 or amount > max_amount:
            raise ValidationFailed("stars amount out of range", min=50, max=max_amount)
        ton_usd, usd_uzs, margin, _, _ = await self._common()
        unit_ton_raw = await self.settings.get("provider.star_unit_cost_ton")
        markup = D(await self.settings.get("pricing.stars.markup_percent"))
        if unit_ton_raw:
            cost = D(unit_ton_raw) * amount * ton_usd
        else:
            cost = D(await self.settings.get("pricing.fallback_star_cost_usd")) * amount
        min_price = cost * (1 + margin / 100)
        price = round_up(max(cost * (1 + markup / 100), min_price), Decimal("0.01"))
        q = self._finish(price, cost, min_price, ton_usd, usd_uzs, 0)
        return self._apply_promo(q, promo, Decimal("0.01"))

    async def quote_topup(self, amount_usd: Decimal) -> Quote:
        lo, hi = (
            D(await self.settings.get("pricing.topup.min_usd")),
            D(await self.settings.get("pricing.topup.max_usd")),
        )
        if not lo <= amount_usd <= hi:
            raise ValidationFailed("topup out of range", min=str(lo), max=str(hi))
        ton_usd, usd_uzs, _, _, star_rate = await self._common()
        price = quantize(amount_usd)
        return self._finish(price, price, price, ton_usd, usd_uzs, int(ceil_places(price / star_rate, 0)))

    def _apply_promo(self, q: Quote, promo: PromoCode | None, step: Decimal) -> Quote:
        if promo is None:
            return q
        discount = PromoService.discount_for(promo, q.price_usd)
        # never below the minimum margin; keep prices on a clean 0.01 grid and never above the undiscounted price
        new_price = min(round_up(max(q.price_usd - discount, q.min_price_usd), Decimal("0.01")), q.price_usd)
        discount = quantize(q.price_usd - new_price)
        q.discount_usd = discount
        q.price_usd = quantize(new_price)
        q.price_ton = ceil_places(q.price_usd / q.ton_usd, 2)
        q.price_uzs = round_to(q.price_usd * q.usd_uzs, 1000)
        if q.price_xtr and q.discount_usd:
            ratio = q.price_usd / (q.price_usd + q.discount_usd)
            q.price_xtr = max(1, int(q.price_xtr * ratio))
        return q
