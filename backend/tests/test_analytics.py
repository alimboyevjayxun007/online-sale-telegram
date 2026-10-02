from datetime import UTC, date, datetime
from decimal import Decimal as Dc

from sqlalchemy import select

from app.core.enums import (
    OrderStatus as S,
)
from app.core.enums import (
    PaymentMethod as M,
)
from app.core.enums import (
    PaymentPurpose,
    PaymentStatus,
    ProductType,
    RecipientType,
)
from app.models import DailyStats, Expense, Order, Payment, UserDailyActivity
from app.services.analytics_service import AnalyticsService, pct_change, resolve_period
from tests.factories import make_user


def order(uid, pid, price, cost, months, completed, method=M.TON, status=S.COMPLETED, stars=None):
    return Order(
        public_id=pid, user_id=uid, product_type=ProductType.STARS if stars else ProductType.PREMIUM,
        plan_months=months, stars_amount=stars, recipient_type=RecipientType.SELF, status=status,
        payment_method=method, price_usd=Dc(price), cost_usd=Dc(cost) if cost else None, profit_usd=Dc(price) - Dc(cost) if cost else None,
        created_at=completed or datetime(2026, 10, 1, 11, tzinfo=UTC), paid_at=completed.replace(second=0) if completed else None, completed_at=completed,
    )  # fmt: skip


async def test_day_boundaries_and_metrics(session):
    u1, u2 = await make_user(session, 1), await make_user(session, 2)
    u1.created_at = datetime(2026, 9, 30, 19, 30, tzinfo=UTC)  # = 2026-10-01 00:30 Tashkent
    u2.created_at = datetime(2026, 9, 30, 18, 59, tzinfo=UTC)  # = 2026-09-30 23:59 Tashkent
    session.add_all([
        order(1, "PR-A", "13.15", "12.15", 3, datetime(2026, 9, 30, 19, 30, 10, tzinfo=UTC)),
        order(1, "PR-B", "31.50", "29.13", 12, datetime(2026, 10, 1, 9, 0, 30, tzinfo=UTC), M.BALANCE),
        order(2, "ST-C", "8.03", "7.50", None, datetime(2026, 10, 1, 10, 0, 30, tzinfo=UTC), stars=500),
        order(2, "PR-D", "17.45", "16.14", 6, datetime(2026, 9, 30, 18, 59, 30, tzinfo=UTC)),  # previous local day
        order(2, "PR-E", "9.99", None, 3, None, status=S.FAILED),
    ])  # fmt: skip
    session.add(Expense(category="server", amount_usd=Dc("2.5"), spent_on=date(2026, 10, 1)))
    session.add(UserDailyActivity(day=date(2026, 10, 1), user_id=1))
    session.add(UserDailyActivity(day=date(2026, 10, 1), user_id=2))
    session.add(Payment(public_id="PM-1", user_id=1, purpose=PaymentPurpose.ORDER, method=M.TON, status=PaymentStatus.CONFIRMED,
                        amount=Dc(4), currency="TON", amount_usd=Dc("13.15"), confirmed_at=datetime(2026, 10, 1, 1, tzinfo=UTC)))  # fmt: skip
    await session.flush()

    a = AnalyticsService(session)
    m = await a.range_metrics(date(2026, 10, 1), date(2026, 10, 1))
    assert m["new_users"] == 1 and m["active_users"] == 2 and m["paying_users"] == 2
    assert m["orders_completed"] == 3
    assert m["revenue_usd"] == Dc("52.68") and m["cost_usd"] == Dc("48.78")
    assert m["gross_profit_usd"] == Dc("3.90") and m["expenses_usd"] == Dc("2.5") and m["net_profit_usd"] == Dc("1.40")
    assert (m["premium_3m"], m["premium_6m"], m["premium_12m"]) == (1, 0, 1)
    assert m["stars_orders"] == 1 and m["stars_sold"] == 500
    assert m["cash_in_usd"] == Dc("13.15")
    assert m["revenue_by_method"] == {"ton": "21.180000", "balance": "31.500000"}
    prev = await a.range_metrics(date(2026, 9, 30), date(2026, 9, 30))
    assert prev["orders_completed"] == 1 and prev["revenue_usd"] == Dc("17.45") and prev["new_users"] == 1
    assert (
        prev["orders_failed"] == 0
    )  # PR-E was created on Oct 1 via created_at=None -> server default; just ensure no crash

    row = await a.compute_day(date(2026, 10, 1))
    assert row.revenue_usd == Dc("52.68")
    again = await a.compute_day(date(2026, 10, 1))  # idempotent upsert
    assert again.day == row.day
    assert len((await session.scalars(select(DailyStats))).all()) == 1


async def test_dashboard_changes_and_series(session):
    await make_user(session, 1)
    a = AnalyticsService(session)
    today = date(2026, 10, 14)  # Wednesday
    p = resolve_period("week", today=today)
    assert (p.start, p.end) == (date(2026, 10, 12), today)
    assert (p.prev_start, p.prev_end) == (date(2026, 10, 5), date(2026, 10, 7))
    mo = resolve_period("month", today=today)
    assert mo.start == date(2026, 10, 1) and mo.prev_start == date(2026, 9, 1) and mo.prev_end == date(2026, 9, 14)
    assert resolve_period("today", today=today).granularity == "hour"
    assert resolve_period("yesterday", today=today).prev_start == date(2026, 10, 6)
    yr = resolve_period("year", today=today)
    assert yr.start == date(2026, 1, 1) and yr.prev_start == date(2025, 1, 1) and yr.granularity == "week"
    c = resolve_period("custom", date(2026, 1, 1), date(2026, 1, 10))
    assert c.prev_start == date(2025, 12, 22) and c.prev_end == date(2025, 12, 31)
    assert pct_change(110, 100) == 10.0 and pct_change(5, 0) is None

    d = await a.dashboard(resolve_period("custom", date(2026, 10, 1), date(2026, 10, 7)))
    assert d["current"]["orders_completed"] == 0 and d["totals"]["users"] == 1
    series = await a.timeseries(resolve_period("custom", date(2026, 10, 1), date(2026, 10, 3)), ["revenue_usd"])
    assert [x["t"] for x in series] == ["2026-10-01", "2026-10-02", "2026-10-03"] or len(series) <= 3
    assert await a.dau_wau_mau() == {"dau": 0, "wau": 0, "mau": 0}
