from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.money import quantize
from app.models import PremiumPlan, StarPackage
from app.services.pricing_service import PricingService, Quote
from app.services.rate_service import RateService
from app.services.settings_service import SettingsService


def quote_dict(q: Quote) -> dict[str, Any]:
    return {
        "price_usd": str(quantize(q.price_usd)),
        "price_ton": str(q.price_ton),
        "price_xtr": q.price_xtr,
        "price_uzs": q.price_uzs,
        "discount_usd": str(quantize(q.discount_usd)),
    }


class CatalogService:
    def __init__(
        self, session: AsyncSession, settings: SettingsService, pricing: PricingService, rates: RateService
    ) -> None:
        self.session, self.settings, self.pricing, self.rates = session, settings, pricing, rates

    async def methods(self) -> dict[str, bool]:
        return {
            "ton": bool(await self.settings.get("payments.ton.enabled")),
            "stars": bool(await self.settings.get("payments.stars.enabled")),
            "balance": bool(await self.settings.get("payments.balance.enabled")),
            "topup_stars": bool(await self.settings.get("payments.topup.stars.enabled")),
        }

    async def plans(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        plans = (
            await self.session.scalars(select(PremiumPlan).order_by(PremiumPlan.sort_order, PremiumPlan.months))
        ).all()
        for p in plans:
            item: dict[str, Any] = {
                "id": p.id,
                "months": p.months,
                "badge": p.badge,
                "available": False,
                "coming_soon": not p.provider_supported,
                "reference_price_usd": str(p.reference_price_usd) if p.reference_price_usd else None,
            }
            if p.is_enabled and p.provider_supported:
                try:
                    q = await self.pricing.quote_premium(p)
                    item.update(available=True, **quote_dict(q))
                    if p.reference_price_usd and p.reference_price_usd > 0:
                        item["saving_pct"] = int((p.reference_price_usd - q.price_usd) / p.reference_price_usd * 100)
                except AppError:
                    pass
            if item["available"] or item["coming_soon"]:
                out.append(item)
        return out

    async def star_packages(self) -> list[dict[str, Any]]:
        pkgs = (
            await self.session.scalars(
                select(StarPackage)
                .where(StarPackage.is_enabled.is_(True))
                .order_by(StarPackage.sort_order, StarPackage.amount)
            )
        ).all()
        return [
            {
                "id": p.id,
                "amount": p.amount,
                "popular": p.is_popular,
                **quote_dict(await self.pricing.quote_stars(p.amount)),
            }
            for p in pkgs
        ]

    async def catalog(self) -> dict[str, Any]:
        return {
            "plans": await self.plans(),
            "star_packages": await self.star_packages(),
            "methods": await self.methods(),
            "rates": {"ton_usd": str(await self.rates.ton_usd()), "usd_uzs": str(await self.rates.usd_uzs())},
            "stars_max": int(await self.settings.get("pricing.stars.max_amount")),
            "support_username": str(await self.settings.get("bot.support_username") or ""),
        }
