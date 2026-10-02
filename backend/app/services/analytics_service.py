from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import Date, cast, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import OrderStatus, PaymentMethod, PaymentStatus, RewardStatus
from app.core.money import D, quantize
from app.core.timeutil import day_bounds_utc, now_utc, today_local, tz
from app.models import (
    DailyStats,
    Expense,
    Order,
    Payment,
    ReferralReward,
    User,
    UserDailyActivity,
)

Z = Decimal(0)
SUM_FIELDS = [
    "new_users", "orders_created", "orders_completed", "orders_failed", "orders_refunded", "premium_3m",
    "premium_6m", "premium_12m", "stars_orders", "stars_sold", "cash_in_usd", "revenue_usd", "cost_usd",
    "gross_profit_usd", "expenses_usd", "referral_usd", "net_profit_usd",
]  # fmt: skip


@dataclass
class Period:
    start: date  # inclusive local date
    end: date  # inclusive local date
    prev_start: date
    prev_end: date
    granularity: str  # hour | day | week | month


def resolve_period(name: str, frm: date | None = None, to: date | None = None, today: date | None = None) -> Period:
    today = today or today_local()
    if name == "today":
        s = e = today
    elif name == "yesterday":
        s = e = today - timedelta(days=1)
    elif name == "week":
        s, e = today - timedelta(days=today.weekday()), today
    elif name == "month":
        s, e = today.replace(day=1), today
    elif name == "year":
        s, e = today.replace(month=1, day=1), today
    elif name == "custom" and frm and to and frm <= to:
        s, e = frm, to
    else:
        raise ValueError(f"bad period {name}")
    days = (e - s).days + 1
    if name in ("today", "yesterday"):
        ps = pe = s - timedelta(days=1)
        if name == "yesterday":
            ps = pe = s - timedelta(days=7)  # same weekday last week
    elif name == "week":
        ps, pe = s - timedelta(days=7), s - timedelta(days=7) + (e - s)
    elif name == "month":
        pe = s - timedelta(days=1)
        ps = pe.replace(day=1)
        pe = min(ps + (e - s), pe)
    elif name == "year":
        ps = s.replace(year=s.year - 1)
        pe = min(
            e.replace(year=e.year - 1) if not (e.month == 2 and e.day == 29) else date(e.year - 1, 2, 28),
            date(s.year - 1, 12, 31),
        )
    else:
        pe = s - timedelta(days=1)
        ps = pe - timedelta(days=days - 1)
    gran = "hour" if days <= 2 else "day" if days <= 90 else "week" if days <= 365 else "month"
    return Period(s, e, ps, pe, gran)


def pct_change(cur: Decimal | int, prev: Decimal | int) -> float | None:
    if not prev:
        return None
    return float((D(cur) - D(prev)) / D(prev) * 100)


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ---------- raw aggregation for a local-date range ----------
    async def range_metrics(self, start: date, end: date) -> dict[str, Any]:
        lo, _ = day_bounds_utc(start)
        _, hi = day_bounds_utc(end)
        s = self.session
        completed = (Order.status == OrderStatus.COMPLETED, Order.completed_at >= lo, Order.completed_at < hi)
        created = (Order.created_at >= lo, Order.created_at < hi)

        async def one(stmt: Any) -> Any:
            return (await s.execute(stmt)).one()

        users = await s.scalar(
            select(func.count()).select_from(User).where(User.created_at >= lo, User.created_at < hi)
        )
        active = await s.scalar(
            select(func.count(func.distinct(UserDailyActivity.user_id))).where(
                UserDailyActivity.day >= start, UserDailyActivity.day <= end
            )
        )
        r = await one(
            select(
                func.count(),
                func.coalesce(func.sum(Order.price_usd), 0),
                func.coalesce(func.sum(Order.cost_usd), 0),
                func.count(func.distinct(Order.user_id)),
                func.avg(func.extract("epoch", Order.completed_at - Order.paid_at)),
                func.count().filter(Order.plan_months == 3),
                func.count().filter(Order.plan_months == 6),
                func.count().filter(Order.plan_months == 12),
                func.count().filter(Order.stars_amount.is_not(None)),
                func.coalesce(func.sum(Order.stars_amount), 0),
            ).where(*completed)
        )  # fmt: skip
        n_done, revenue, cost, paying, avg_deliv, p3, p6, p12, st_orders, st_sold = r
        by_method_rows = (
            await s.execute(
                select(Order.payment_method, func.sum(Order.price_usd)).where(*completed).group_by(Order.payment_method)
            )
        ).all()
        created_rows = dict(
            (await s.execute(select(Order.status, func.count()).where(*created).group_by(Order.status))).all()
        )
        cash_in = await s.scalar(
            select(func.coalesce(func.sum(Payment.amount_usd), 0)).where(
                Payment.status == PaymentStatus.CONFIRMED,
                Payment.method != PaymentMethod.BALANCE,
                Payment.confirmed_at >= lo,
                Payment.confirmed_at < hi,
            )
        )
        expenses = await s.scalar(
            select(func.coalesce(func.sum(Expense.amount_usd), 0)).where(
                Expense.spent_on >= start, Expense.spent_on <= end
            )
        )
        referral = await s.scalar(
            select(func.coalesce(func.sum(ReferralReward.amount_usd), 0)).where(
                ReferralReward.status == RewardStatus.CREDITED,
                ReferralReward.created_at >= lo,
                ReferralReward.created_at < hi,
            )
        )
        revenue, cost, cash_in, expenses, referral = (D(x or 0) for x in (revenue, cost, cash_in, expenses, referral))
        gross = revenue - cost
        return {
            "new_users": users or 0,
            "active_users": active or 0,
            "paying_users": paying or 0,
            "orders_created": sum(created_rows.values()),
            "orders_completed": n_done,
            "orders_failed": created_rows.get(OrderStatus.FAILED, 0) + created_rows.get(OrderStatus.NEEDS_REVIEW, 0),
            "orders_refunded": created_rows.get(OrderStatus.REFUNDED, 0),
            "premium_3m": p3, "premium_6m": p6, "premium_12m": p12,
            "stars_orders": st_orders, "stars_sold": int(st_sold),
            "cash_in_usd": quantize(cash_in),
            "revenue_usd": quantize(revenue),
            "cost_usd": quantize(cost),
            "gross_profit_usd": quantize(gross),
            "expenses_usd": quantize(expenses),
            "referral_usd": quantize(referral),
            "net_profit_usd": quantize(gross - expenses - referral),
            "revenue_by_method": {m.value: str(quantize(D(v))) for m, v in by_method_rows},
            "avg_delivery_seconds": quantize(D(avg_deliv), "0.01") if avg_deliv is not None else None,
        }  # fmt: skip

    async def compute_day(self, day: date) -> DailyStats:
        m = await self.range_metrics(day, day)
        stmt = insert(DailyStats).values(day=day, **m)
        stmt = stmt.on_conflict_do_update(index_elements=["day"], set_={**m, "updated_at": now_utc()})
        await self.session.execute(stmt)
        return (
            await self.session.scalars(
                select(DailyStats).where(DailyStats.day == day).execution_options(populate_existing=True)
            )
        ).one()

    async def ensure_days(self, start: date, end: date) -> None:
        """Fill missing day rows; always refresh today and yesterday (they can still change)."""
        have = set(
            (
                await self.session.scalars(select(DailyStats.day).where(DailyStats.day >= start, DailyStats.day <= end))
            ).all()
        )
        today = today_local()
        d = start
        while d <= min(end, today):
            if d not in have or d >= today - timedelta(days=1):
                await self.compute_day(d)
            d += timedelta(days=1)

    # ---------- dashboard / comparison ----------
    async def dashboard(self, period: Period) -> dict[str, Any]:
        cur = await self.range_metrics(period.start, period.end)
        prev = await self.range_metrics(period.prev_start, period.prev_end)
        change = {k: pct_change(cur[k], prev[k]) for k in SUM_FIELDS + ["active_users", "paying_users"]}
        total_users = await self.session.scalar(select(func.count()).select_from(User))
        blocked = await self.session.scalar(select(func.count()).select_from(User).where(User.is_bot_blocked.is_(True)))
        pending_review = await self.session.scalar(
            select(func.count()).select_from(Order).where(Order.status == OrderStatus.NEEDS_REVIEW)
        )
        liabilities = await self.session.scalar(select(func.coalesce(func.sum(User.balance_usd), 0)).select_from(User))
        margin = (cur["gross_profit_usd"] / cur["revenue_usd"] * 100) if cur["revenue_usd"] else Z
        aov = (cur["revenue_usd"] / cur["orders_completed"]) if cur["orders_completed"] else Z
        done, bad = cur["orders_completed"], cur["orders_failed"] + cur["orders_refunded"]
        return {
            "period": {
                "start": period.start.isoformat(),
                "end": period.end.isoformat(),
                "granularity": period.granularity,
            },
            "current": cur,
            "previous": prev,
            "change_pct": change,
            "derived": {
                "margin_pct": float(round(margin, 2)),
                "avg_order_usd": str(quantize(aov, "0.01")),
                "success_rate_pct": float(round(D(done) / D(done + bad) * 100, 2)) if done + bad else None,
                "conversion_pct": float(round(D(cur["paying_users"]) / D(cur["new_users"]) * 100, 2))
                if cur["new_users"]
                else None,
            },
            "totals": {
                "users": total_users or 0,
                "blocked_users": blocked or 0,
                "needs_review": pending_review or 0,
                "user_balances_usd": str(quantize(D(liabilities or 0))),
            },
        }

    async def timeseries(self, period: Period, metrics: list[str]) -> list[dict[str, Any]]:
        if period.granularity == "hour":
            return await self._hourly(period)
        await self.ensure_days(period.start, period.end)
        rows = (
            await self.session.scalars(
                select(DailyStats)
                .where(DailyStats.day >= period.start, DailyStats.day <= period.end)
                .order_by(DailyStats.day)
            )
        ).all()
        buckets: dict[date, dict[str, Any]] = {}
        for r in rows:
            key = (
                r.day
                if period.granularity == "day"
                else r.day - timedelta(days=r.day.weekday())
                if period.granularity == "week"
                else r.day.replace(day=1)
            )
            b = buckets.setdefault(key, {m: Z for m in metrics})
            for m in metrics:
                b[m] += D(getattr(r, m) or 0)
        return [{"t": k.isoformat(), **{m: str(v) for m, v in b.items()}} for k, b in sorted(buckets.items())]

    async def _hourly(self, period: Period) -> list[dict[str, Any]]:
        lo, _ = day_bounds_utc(period.start)
        _, hi = day_bounds_utc(period.end)
        hour = func.date_trunc("hour", func.timezone(str(tz()), Order.completed_at))
        rows = (
            await self.session.execute(
                select(
                    hour, func.count(), func.sum(Order.price_usd), func.sum(Order.cost_usd), func.sum(Order.profit_usd)
                )
                .where(Order.status == OrderStatus.COMPLETED, Order.completed_at >= lo, Order.completed_at < hi)
                .group_by(hour)
                .order_by(hour)
            )
        ).all()
        return [
            {"t": h.isoformat(), "orders_completed": str(n), "revenue_usd": str(D(rev or 0)), "cost_usd": str(D(cost or 0)),
             "gross_profit_usd": str(D(profit or 0))}
            for h, n, rev, cost, profit in rows
        ]  # fmt: skip

    # ---------- breakdowns & rankings ----------
    async def breakdown(self, by: str, start: date, end: date) -> list[dict[str, Any]]:
        lo, _ = day_bounds_utc(start)
        _, hi = day_bounds_utc(end)
        col = {
            "product": Order.product_type,
            "method": Order.payment_method,
            "provider": Order.provider,
        }.get(by)
        where = (Order.status == OrderStatus.COMPLETED, Order.completed_at >= lo, Order.completed_at < hi)
        stmt: Any
        if by == "language":
            stmt = (
                select(User.language, func.count(), func.sum(Order.price_usd))
                .join(User, User.id == Order.user_id)
                .where(*where)
                .group_by(User.language)
            )
        elif by == "source":
            stmt = (
                select(func.coalesce(User.source, "organic"), func.count(), func.sum(Order.price_usd))
                .join(User, User.id == Order.user_id)
                .where(*where)
                .group_by(func.coalesce(User.source, "organic"))
            )
        elif col is not None:
            stmt = select(col, func.count(), func.sum(Order.price_usd)).where(*where).group_by(col)
        else:
            raise ValueError(by)
        rows = (await self.session.execute(stmt)).all()
        return [
            {"key": getattr(k, "value", k) or "-", "orders": n, "revenue_usd": str(quantize(D(v or 0)))}
            for k, n, v in rows
        ]

    async def top_buyers(self, start: date, end: date, limit: int = 10) -> list[dict[str, Any]]:
        lo, _ = day_bounds_utc(start)
        _, hi = day_bounds_utc(end)
        rows = (
            await self.session.execute(
                select(User.id, User.username, User.first_name, func.count(), func.sum(Order.price_usd))
                .join(User, User.id == Order.user_id)
                .where(Order.status == OrderStatus.COMPLETED, Order.completed_at >= lo, Order.completed_at < hi)
                .group_by(User.id)
                .order_by(func.sum(Order.price_usd).desc())
                .limit(limit)
            )
        ).all()
        return [
            {"id": i, "username": u, "name": n, "orders": c, "spent_usd": str(quantize(D(v)))} for i, u, n, c, v in rows
        ]

    async def top_referrers(self, limit: int = 10) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(ReferralReward.referrer_id, func.count(), func.sum(ReferralReward.amount_usd))
                .where(ReferralReward.status == RewardStatus.CREDITED)
                .group_by(ReferralReward.referrer_id)
                .order_by(func.sum(ReferralReward.amount_usd).desc())
                .limit(limit)
            )
        ).all()
        return [{"id": i, "rewards": c, "earned_usd": str(quantize(D(v)))} for i, c, v in rows]

    async def dau_wau_mau(self) -> dict[str, int]:
        today = today_local()
        out = {}
        for name, days in (("dau", 1), ("wau", 7), ("mau", 30)):
            out[name] = (
                await self.session.scalar(
                    select(func.count(func.distinct(UserDailyActivity.user_id))).where(
                        UserDailyActivity.day > today - timedelta(days=days)
                    )
                )
            ) or 0
        return out

    async def new_users_series(self, start: date, end: date) -> list[dict[str, Any]]:
        lo, _ = day_bounds_utc(start)
        _, hi = day_bounds_utc(end)
        day = cast(func.timezone(str(tz()), User.created_at), Date)
        rows = (
            await self.session.execute(
                select(day, func.count()).where(User.created_at >= lo, User.created_at < hi).group_by(day).order_by(day)
            )
        ).all()
        return [{"t": d.isoformat(), "new_users": n} for d, n in rows]


def local_range_for(period: Period) -> tuple[datetime, datetime]:
    return day_bounds_utc(period.start)[0], day_bounds_utc(period.end)[1]
