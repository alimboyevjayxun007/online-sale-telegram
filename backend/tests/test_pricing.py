import asyncio
from decimal import Decimal as Dc

import pytest

from app.core.db import session_maker
from app.core.enums import BalanceTxType, ProductScope, ProductType, PromoType
from app.core.errors import InsufficientBalance, PlanUnavailable, PromoInvalid, ValidationFailed
from app.core.redis import get_redis
from app.models import PremiumPlan, PromoCode
from app.services.balance_service import BalanceService
from app.services.pricing_service import PricingService
from app.services.promo_service import PromoService
from app.services.rate_service import RateService
from app.services.settings_service import SettingsService
from tests.factories import make_user


async def pricing(session, ton=Dc(3), uzs=Dc(12800)):
    rs = RateService(session, get_redis())
    await rs.set_rate("TON_USD", ton, "t")
    await rs.set_rate("USD_UZS", uzs, "t")
    return PricingService(rs, SettingsService(session))


def plan(months=3, cost="4.0", **kw):
    d = dict(
        months=months,
        is_enabled=True,
        provider_supported=True,
        cost_ton=Dc(cost) if cost is not None else None,
        markup_percent=Dc(8),
        fixed_markup_usd=Dc(0),
        price_stars=1100,
    )
    d.update(kw)
    return PremiumPlan(**d)


@pytest.mark.parametrize(
    "months,cost,markup,fixed,ton,expected",
    [
        (3, "4.0", 8, None, 3, "13.15"),  # 12.15*1.08=13.122 -> 13.15
        (6, "5.33", 8, None, 3, "17.45"),  # 16.14*1.08=17.43 -> 17.45
        (12, "9.66", 8, None, 3, "31.50"),  # 29.13*1.08=31.46 -> 31.50
        (3, "4.0", 0, None, 3, "12.40"),  # markup 0 -> min margin 2%: 12.393 -> 12.40
        (3, "4.0", 8, "20", 3, "20.00"),  # fixed price
        (3, "4.0", 8, "5", 3, "12.40"),  # fixed price below cost clamps to min margin
        (3, "4.0", 8, None, 6, "26.25"),  # TON doubled in price
    ],
)
async def test_premium_price_table(session, months, cost, markup, fixed, ton, expected):
    p = await pricing(session, ton=Dc(ton))
    q = await p.quote_premium(
        plan(months, cost, markup_percent=Dc(markup), fixed_price_usd=Dc(fixed) if fixed else None)
    )
    assert q.price_usd == Dc(expected)
    assert q.price_usd >= q.min_price_usd
    assert q.price_ton * q.ton_usd >= q.price_usd - Dc("0.05")


async def test_premium_unavailable_and_uzs(session):
    p = await pricing(session)
    with pytest.raises(PlanUnavailable):
        await p.quote_premium(plan(1, is_enabled=False))
    with pytest.raises(PlanUnavailable):
        await p.quote_premium(plan(1, cost=None))
    q = await p.quote_premium(plan())
    assert q.price_uzs == 168000 and q.price_ton == Dc("4.39") and q.price_xtr == 1100


@pytest.mark.parametrize("amount,expected", [(50, "0.81"), (500, "8.03"), (1000, "16.05")])
async def test_stars_price(session, amount, expected):
    p = await pricing(session)
    assert (await p.quote_stars(amount)).price_usd == Dc(expected)


@pytest.mark.parametrize("bad", [49, 0, 100001])
async def test_stars_range(session, bad):
    with pytest.raises(ValidationFailed):
        await (await pricing(session)).quote_stars(bad)


async def test_promo_never_below_min_margin(session):
    p = await pricing(session)
    base = await p.quote_premium(plan())
    promo = PromoCode(code="BIG", type=PromoType.PERCENT, value=Dc(90), applies_to=ProductScope.ALL)
    q = await p.quote_premium(plan(), promo)
    assert (
        q.price_usd == Dc("12.40")
        and q.price_usd >= base.min_price_usd
        and q.discount_usd == base.price_usd - Dc("12.40")
    )
    small = PromoCode(code="S", type=PromoType.FIXED_USD, value=Dc("0.5"), applies_to=ProductScope.ALL)
    assert (await p.quote_premium(plan(), small)).price_usd == base.price_usd - Dc("0.5")


async def test_promo_validation(session):
    u = await make_user(session)
    svc = PromoService(session)
    session.add(
        PromoCode(
            code="kuz5",
            type=PromoType.PERCENT,
            value=Dc(5),
            max_uses=1,
            per_user_limit=1,
            applies_to=ProductScope.PREMIUM,
        )
    )
    await session.flush()
    with pytest.raises(PromoInvalid):
        await svc.validate("nope", u.id, ProductType.PREMIUM, Dc(10))
    with pytest.raises(PromoInvalid):
        await svc.validate("KUZ5", u.id, ProductType.STARS, Dc(10))
    promo = await svc.validate("KUZ5", u.id, ProductType.PREMIUM, Dc(10))
    assert PromoService.discount_for(promo, Dc(10)) == Dc("0.5")
    promo.used_count = 1
    with pytest.raises(PromoInvalid):
        await svc.validate("KUZ5", u.id, ProductType.PREMIUM, Dc(10))


async def test_balance_ledger_and_limits(session):
    u = await make_user(session)
    b = BalanceService(session)
    await b.credit(u.id, Dc(10), BalanceTxType.TOPUP)
    tx = await b.debit(u.id, Dc("3.5"), BalanceTxType.PURCHASE)
    assert tx.balance_after == Dc("6.5") and u.balance_usd == Dc("6.5")
    with pytest.raises(InsufficientBalance):
        await b.debit(u.id, Dc(100), BalanceTxType.PURCHASE)


async def test_parallel_debits_never_negative(session):
    u = await make_user(session)
    await BalanceService(session).credit(u.id, Dc(10), BalanceTxType.TOPUP)
    await session.commit()

    async def spend():
        async with session_maker()() as s:
            try:
                await BalanceService(s).debit(u.id, Dc(3), BalanceTxType.PURCHASE)
                await s.commit()
                return 1
            except InsufficientBalance:
                return 0

    ok = sum(await asyncio.gather(*[spend() for _ in range(8)]))
    assert ok == 3
    await session.refresh(u)
    assert u.balance_usd == Dc(1)


async def test_fallback_usd_cost_when_no_live_price(session):
    p = await pricing(session, ton=Dc(3))
    q = await p.quote_premium(plan(3, cost=None))
    assert q.cost_usd == Dc("12.14") and q.price_usd == Dc("13.15")  # 11.99 + 0.05 TON fee
    assert (await p.quote_premium(plan(6, cost=None))).price_usd == Dc("17.45")
    # the fallback is a USD list price: a pricier TON makes the TON amount smaller, the USD cost stays put
    p2 = await pricing(session, ton=Dc(6))
    q2 = await p2.quote_premium(plan(3, cost=None))
    assert q2.price_ton < q.price_ton
    # a live price from the provider wins over the fallback
    live = await p2.quote_premium(plan(3, cost="3.0"))
    assert live.cost_usd == Dc("18.3")  # (3.0 + 0.05 TON fee) * 6 — the live TON price, not the USD fallback
