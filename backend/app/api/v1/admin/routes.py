from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Query, Response
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import AdminActor, OwnerActor, Session, SupportActor
from app.api.runtime import Services, build_providers, runtime
from app.api.v1.shop import order_dict, payment_dict
from app.core.config import get_settings
from app.core.enums import (
    AdminRole,
    BroadcastStatus,
    ExpenseCategory,
    OrderStatus,
    PaymentMethod,
    ProductScope,
    PromoType,
)
from app.core.errors import NotFound, ValidationFailed
from app.core.money import D, quantize
from app.core.redis import get_redis
from app.models import (
    AuditLog,
    Channel,
    Expense,
    HotWalletTransaction,
    Order,
    Payment,
    PromoCode,
    StarsTransaction,
    UnmatchedTonTx,
    User,
)
from app.services.admin_service import AdminService
from app.services.analytics_service import AnalyticsService, resolve_period
from app.services.balance_service import BalanceService
from app.services.broadcast_service import BroadcastService
from app.services.export_service import ExportService
from app.services.order_service import OrderService
from app.services.settings_service import DEFAULTS, SettingsService
from app.services.user_service import UserService

router = APIRouter(prefix="/admin", tags=["admin"])


def _period(period: str, frm: date | None, to: date | None):  # type: ignore[no-untyped-def]
    try:
        return resolve_period(period, frm, to)
    except ValueError as exc:
        raise ValidationFailed(str(exc)) from exc


# ---------- dashboard & stats ----------
@router.get("/dashboard")
async def dashboard(
    actor: AdminActor, session: Session, period: str = "today", frm: date | None = None, to: date | None = None
) -> dict[str, Any]:
    svc = Services(session)
    p = _period(period, frm, to)
    data = await AnalyticsService(session).dashboard(p)
    data["activity"] = await AnalyticsService(session).dau_wau_mau()
    wallet: dict[str, Any] = {"address": await svc.settings.get("hot_wallet.address")}
    try:
        hw = svc.hot_wallet()
        wallet["balance_ton"] = str(await hw.balance()) if wallet["address"] else None
        wallet["withdrawable_ton"] = str(await hw.withdrawable()) if wallet["address"] else None
    except Exception:  # noqa: BLE001 - chain API down must not break the dashboard
        wallet["balance_ton"] = None
    stars_in = await session.scalar(
        select(func.coalesce(func.sum(StarsTransaction.amount), 0)).where(StarsTransaction.direction == "in")
    )
    stars_out = await session.scalar(
        select(func.coalesce(func.sum(StarsTransaction.amount), 0)).where(StarsTransaction.direction == "out")
    )
    data["wallets"] = {"hot_wallet": wallet, "stars_ledger": int((stars_in or 0) - (stars_out or 0))}
    if runtime().stars is not None:
        try:
            data["wallets"]["stars_balance"] = await runtime().stars.star_balance()  # type: ignore[union-attr]
        except Exception:  # noqa: BLE001
            data["wallets"]["stars_balance"] = None
    return data


@router.get("/stats/timeseries")
async def timeseries(actor: AdminActor, session: Session, period: str = "month", frm: date | None = None, to: date | None = None,
                     metrics: str = "revenue_usd,cost_usd,gross_profit_usd,orders_completed") -> list[dict[str, Any]]:  # fmt: skip
    wanted = [m for m in metrics.split(",") if m]
    from app.models import DailyStats

    valid = {c.name for c in DailyStats.__table__.columns} - {
        "day",
        "updated_at",
        "revenue_by_method",
        "avg_delivery_seconds",
    }
    if not set(wanted) <= valid:
        raise ValidationFailed("unknown metric")
    return await AnalyticsService(session).timeseries(_period(period, frm, to), wanted)


@router.get("/stats/breakdown")
async def breakdown(
    actor: AdminActor,
    session: Session,
    by: str = "product",
    period: str = "month",
    frm: date | None = None,
    to: date | None = None,
) -> list[dict[str, Any]]:
    p = _period(period, frm, to)
    try:
        return await AnalyticsService(session).breakdown(by, p.start, p.end)
    except ValueError as exc:
        raise ValidationFailed("by") from exc


@router.get("/stats/top-buyers")
async def top_buyers(
    actor: AdminActor,
    session: Session,
    period: str = "month",
    frm: date | None = None,
    to: date | None = None,
    limit: int = Query(10, le=50),
) -> list[dict[str, Any]]:
    p = _period(period, frm, to)
    return await AnalyticsService(session).top_buyers(p.start, p.end, limit)


@router.get("/stats/users-growth")
async def users_growth(
    actor: AdminActor, session: Session, period: str = "month", frm: date | None = None, to: date | None = None
) -> list[dict[str, Any]]:
    p = _period(period, frm, to)
    return await AnalyticsService(session).new_users_series(p.start, p.end)


@router.get("/stats/export.xlsx")
async def export_xlsx(
    actor: AdminActor, session: Session, period: str = "month", frm: date | None = None, to: date | None = None
) -> Response:
    data = await ExportService(session).export_period(_period(period, frm, to))
    return Response(data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": 'attachment; filename="stats.xlsx"'})  # fmt: skip


# ---------- orders ----------
@router.get("/orders")
async def orders(actor: SupportActor, session: Session, status: str | None = None, q: str | None = None,
                 limit: int = Query(20, le=100), offset: int = 0) -> dict[str, Any]:  # fmt: skip
    stmt = select(Order).order_by(Order.id.desc()).limit(limit + 1).offset(offset)
    if status in {s.value for s in OrderStatus}:
        stmt = stmt.where(Order.status == OrderStatus(status))
    if q:
        term = q.strip().lstrip("@")
        stmt = stmt.where(
            (Order.public_id == term.upper())
            | (func.lower(Order.recipient_username) == term.lower())
            | (Order.user_id == (int(term) if term.isdigit() else -1))
        )
    rows = (await session.scalars(stmt)).all()
    return {
        "items": [
            {**order_dict(o), "user_id": o.user_id, "provider": o.provider.value if o.provider else None}
            for o in rows[:limit]
        ],
        "has_more": len(rows) > limit,
    }


@router.get("/orders/{public_id}")
async def order_detail(public_id: str, actor: SupportActor, session: Session) -> dict[str, Any]:
    svc = OrderService(session)
    o = await svc.by_public_id(public_id)
    pays = (await session.scalars(select(Payment).where(Payment.order_id == o.id))).all()
    user = await session.get(User, o.user_id)
    return {
        **order_dict(o),
        "user": {
            "id": o.user_id,
            "username": user.username if user else None,
            "name": user.first_name if user else None,
        },
        "cost_usd": str(o.cost_usd) if o.cost_usd is not None else None,
        "profit_usd": str(o.profit_usd) if o.profit_usd is not None else None,
        "provider": o.provider.value if o.provider else None,
        "provider_ref": o.provider_ref,
        "error_message": o.error_message,
        "attempts": o.attempts,
        "events": [
            {
                "from": e.from_status.value if e.from_status else None,
                "to": e.to_status.value,
                "actor": e.actor,
                "at": e.created_at.isoformat(),
            }
            for e in await svc.events(o.id)
        ],
        "payments": [payment_dict(p) | {"tx_hash": p.ton_tx_hash} for p in pays],
    }


@router.post("/orders/{public_id}/retry")
async def order_retry(public_id: str, actor: SupportActor, session: Session) -> dict[str, Any]:
    svc = Services(session)
    o = await OrderService(session).by_public_id(public_id)
    await (await svc.fulfillment()).retry(o, f"admin:{actor.id}")
    await svc.settings.get("bot.maintenance")
    from app.services.audit_service import AuditService

    await AuditService(session).log(actor.id, "order.retry", "order", public_id, source="webapp")
    return order_dict(o)


class RefundIn(BaseModel):
    to: str = "auto"  # auto | balance | stars


@router.post("/orders/{public_id}/refund")
async def order_refund(public_id: str, body: RefundIn, actor: AdminActor, session: Session) -> dict[str, Any]:
    svc = Services(session)
    o = await OrderService(session).by_public_id(public_id)
    await (await svc.fulfillment()).refund(o, f"admin:{actor.id}", body.to)
    from app.services.audit_service import AuditService

    await AuditService(session).log(actor.id, "order.refund", "order", public_id, source="webapp")
    return order_dict(o)


class CompleteIn(BaseModel):
    provider_ref: str = "manual"


@router.post("/orders/{public_id}/mark-completed")
async def order_complete(public_id: str, body: CompleteIn, actor: AdminActor, session: Session) -> dict[str, Any]:
    svc = Services(session)
    o = await OrderService(session).by_public_id(public_id)
    await (await svc.fulfillment()).mark_completed_manually(o, f"admin:{actor.id}", body.provider_ref)
    from app.services.audit_service import AuditService

    await AuditService(session).log(actor.id, "order.complete", "order", public_id, source="webapp")
    return order_dict(o)


# ---------- users ----------
@router.get("/users")
async def users(actor: SupportActor, session: Session, q: str | None = None, banned: bool | None = None,
                sort: str = "new", limit: int = Query(20, le=100), offset: int = 0) -> dict[str, Any]:  # fmt: skip
    if q:
        rows = await UserService(session).search(q, limit + 1)
    else:
        stmt = select(User)
        if banned is not None:
            stmt = stmt.where(User.is_banned.is_(banned))
        order_col: Any = {
            "new": User.created_at.desc(),
            "spent": User.total_spent_usd.desc(),
            "balance": User.balance_usd.desc(),
        }.get(sort, User.created_at.desc())
        rows = list((await session.scalars(stmt.order_by(order_col).limit(limit + 1).offset(offset))).all())
    return {"items": [_user_row(u) for u in rows[:limit]], "has_more": len(rows) > limit}


def _user_row(u: User) -> dict[str, Any]:
    return {
        "id": u.id, "username": u.username, "name": u.first_name, "language": u.language,
        "balance_usd": str(quantize(u.balance_usd)), "total_spent_usd": str(quantize(u.total_spent_usd)),
        "orders_count": u.orders_count, "is_banned": u.is_banned, "created_at": u.created_at.isoformat(),
        "last_seen_at": u.last_seen_at.isoformat(), "source": u.source, "referrer_id": u.referrer_id,
    }  # fmt: skip


@router.get("/users/{user_id}")
async def user_detail(user_id: int, actor: SupportActor, session: Session) -> dict[str, Any]:
    u = await UserService(session).get(user_id)
    recent = await OrderService(session).list_for_user(user_id, None, 10, 0)
    invited = await session.scalar(select(func.count()).select_from(User).where(User.referrer_id == user_id))
    ledger = await BalanceService(session).history(user_id, 10)
    return {**_user_row(u), "invited": invited or 0, "ban_reason": u.ban_reason,
            "orders": [order_dict(o) for o in recent],
            "ledger": [{"amount_usd": str(quantize(t.amount_usd)), "type": t.type.value, "at": t.created_at.isoformat()} for t in ledger]}  # fmt: skip


class ReasonIn(BaseModel):
    reason: str | None = None


@router.post("/users/{user_id}/ban")
async def ban(user_id: int, body: ReasonIn, actor: AdminActor, session: Session) -> dict[str, bool]:
    await AdminService(session, SettingsService(session)).ban(actor.id, user_id, body.reason)
    return {"ok": True}


@router.post("/users/{user_id}/unban")
async def unban(user_id: int, actor: AdminActor, session: Session) -> dict[str, bool]:
    await AdminService(session, SettingsService(session)).unban(actor.id, user_id)
    return {"ok": True}


class BalanceIn(BaseModel):
    amount_usd: Decimal
    comment: str | None = None


@router.post("/users/{user_id}/balance")
async def adjust_balance(user_id: int, body: BalanceIn, actor: AdminActor, session: Session) -> dict[str, str]:
    after = await AdminService(session, SettingsService(session)).adjust_balance(
        actor.id, actor.role, user_id, body.amount_usd, body.comment
    )
    return {"balance_usd": str(quantize(after))}


class MessageIn(BaseModel):
    text: str


@router.post("/users/{user_id}/message")
async def message_user(user_id: int, body: MessageIn, actor: SupportActor, session: Session) -> dict[str, bool]:
    svc = Services(session)
    user = await UserService(session).get(user_id)
    await svc.notifier.notify_user(user, "admin_message", text=body.text[:3500])
    return {"ok": True}


# ---------- pricing ----------
@router.get("/pricing/plans")
async def pricing_plans(actor: AdminActor, session: Session) -> list[dict[str, Any]]:
    from app.models import PremiumPlan

    svc = Services(session)
    out = []
    for p in (await session.scalars(select(PremiumPlan).order_by(PremiumPlan.sort_order))).all():
        row: dict[str, Any] = {
            c.name: (str(v) if isinstance(v, Decimal) else v)
            for c in PremiumPlan.__table__.columns
            if (v := getattr(p, c.name)) is not None and c.name != "cost_updated_at"
        }
        row["cost_updated_at"] = p.cost_updated_at.isoformat() if p.cost_updated_at else None
        try:
            q = await svc.pricing.quote_premium(p)
            row["quote"] = {
                "price_usd": str(q.price_usd),
                "cost_usd": str(q.cost_usd),
                "profit_usd": str(quantize(q.price_usd - q.cost_usd)),
                "price_ton": str(q.price_ton),
            }
        except Exception:  # noqa: BLE001 - disabled/unknown cost plans have no quote
            row["quote"] = None
        out.append(row)
    return out


class PlanPatch(BaseModel):
    is_enabled: bool | None = None
    markup_percent: Decimal | None = None
    fixed_markup_usd: Decimal | None = None
    fixed_price_usd: Decimal | None = None
    clear_fixed_price: bool = False
    price_stars: int | None = None
    badge: str | None = None
    reference_price_usd: Decimal | None = None
    cost_ton: Decimal | None = None


@router.put("/pricing/plans/{plan_id}")
async def update_plan(plan_id: int, body: PlanPatch, actor: AdminActor, session: Session) -> dict[str, bool]:
    fields = body.model_dump(exclude_unset=True, exclude={"clear_fixed_price"})
    if body.clear_fixed_price:
        fields["fixed_price_usd"] = None
    await AdminService(session, SettingsService(session)).update_plan(actor.id, plan_id, **fields)
    return {"ok": True}


class PackagesIn(BaseModel):
    packages: list[dict[str, Any]]


@router.put("/pricing/star-packages")
async def set_packages(body: PackagesIn, actor: AdminActor, session: Session) -> dict[str, bool]:
    await AdminService(session, SettingsService(session)).set_star_packages(actor.id, body.packages)
    return {"ok": True}


@router.post("/pricing/refresh")
async def refresh_prices(actor: AdminActor, session: Session) -> dict[str, int]:
    svc = Services(session)
    providers = list((await build_providers(svc.settings, runtime())).values())
    return {"updated": await AdminService(session, svc.settings).refresh_provider_prices(providers)}


# ---------- settings ----------
EDITABLE_PREFIXES = (
    "payments.",
    "pricing.",
    "fulfillment.",
    "referral.",
    "bot.",
    "notify.",
    "hot_wallet.sweep",
    "hot_wallet.reserve",
    "hot_wallet.low",
    "hot_wallet.daily",
)


@router.get("/settings")
async def get_settings_api(actor: AdminActor, session: Session) -> dict[str, Any]:
    return await SettingsService(session).get_all()


class SettingsIn(BaseModel):
    values: dict[str, Any]


@router.put("/settings")
async def put_settings(body: SettingsIn, actor: AdminActor, session: Session) -> dict[str, bool]:
    svc = SettingsService(session)
    from app.services.audit_service import AuditService

    for key, value in body.values.items():
        if key not in DEFAULTS or not key.startswith(EDITABLE_PREFIXES):
            raise ValidationFailed(f"setting {key} is not editable")
        if key.startswith("hot_wallet.sweep") and actor.role != AdminRole.OWNER:
            raise ValidationFailed("only the owner can change sweep settings")
        before = await svc.get(key)
        await svc.set(key, value, actor.id)
        await AuditService(session).log(actor.id, "settings.update", "setting", key, before, value, "webapp")
    return {"ok": True}


class CookiesIn(BaseModel):
    cookies: str


@router.put("/settings/fragment-cookies")
async def put_cookies(body: CookiesIn, actor: OwnerActor, session: Session) -> dict[str, bool]:
    from app.services.audit_service import AuditService

    await SettingsService(session).set("fragment.cookies", body.cookies, actor.id)
    await AuditService(session).log(
        actor.id, "settings.fragment_cookies", "setting", "fragment.cookies", source="webapp"
    )
    return {"ok": True}


# ---------- finance ----------
@router.get("/finance/overview")
async def finance_overview(actor: AdminActor, session: Session) -> dict[str, Any]:
    svc = Services(session)
    s = get_settings()
    out: dict[str, Any] = {"admin_address": s.admin_ton_address, "hot_wallet_address": await svc.settings.get("hot_wallet.address"),
                           "frozen": bool(await svc.settings.get("hot_wallet.frozen")),
                           "sweep_enabled": bool(await svc.settings.get("hot_wallet.sweep_enabled"))}  # fmt: skip
    try:
        hw = svc.hot_wallet()
        out["hot_wallet_ton"] = str(await hw.balance())
        out["withdrawable_ton"] = str(await hw.withdrawable())
    except Exception:  # noqa: BLE001
        out["hot_wallet_ton"] = None
    out["liabilities_usd"] = str(
        quantize(D(await session.scalar(select(func.coalesce(func.sum(User.balance_usd), 0))) or 0))
    )
    stars_in = await session.scalar(
        select(func.coalesce(func.sum(StarsTransaction.amount), 0)).where(StarsTransaction.direction == "in")
    )
    stars_out = await session.scalar(
        select(func.coalesce(func.sum(StarsTransaction.amount), 0)).where(StarsTransaction.direction == "out")
    )
    out["stars_ledger"] = int((stars_in or 0) - (stars_out or 0))
    out["unmatched_pending"] = (
        await session.scalar(
            select(func.count()).select_from(UnmatchedTonTx).where(UnmatchedTonTx.resolution == "pending")
        )
    ) or 0
    return out


class WithdrawIn(BaseModel):
    amount_ton: Decimal


@router.post("/finance/withdraw")
async def withdraw(body: WithdrawIn, actor: OwnerActor, session: Session) -> dict[str, str]:
    tx = await Services(session).hot_wallet().withdraw_to_admin(body.amount_ton, actor.id, actor.role)
    return {"tx_hash": tx}


@router.get("/finance/hot-wallet/transactions")
async def hw_tx(
    actor: AdminActor, session: Session, limit: int = Query(30, le=100), offset: int = 0
) -> list[dict[str, Any]]:
    rows = (
        await session.scalars(
            select(HotWalletTransaction).order_by(HotWalletTransaction.id.desc()).limit(limit).offset(offset)
        )
    ).all()
    return [
        {
            "direction": r.direction.value,
            "kind": r.kind.value,
            "amount_ton": str(r.amount_ton),
            "amount_usd": str(r.amount_usd) if r.amount_usd else None,
            "tx_hash": r.tx_hash,
            "at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/finance/stars/transactions")
async def stars_tx(
    actor: AdminActor, session: Session, limit: int = Query(30, le=100), offset: int = 0
) -> list[dict[str, Any]]:
    rows = (
        await session.scalars(select(StarsTransaction).order_by(StarsTransaction.id.desc()).limit(limit).offset(offset))
    ).all()
    return [
        {"direction": r.direction.value, "kind": r.kind.value, "amount": r.amount, "at": r.created_at.isoformat()}
        for r in rows
    ]


@router.get("/finance/unmatched")
async def unmatched(actor: AdminActor, session: Session) -> list[dict[str, Any]]:
    rows = (
        await session.scalars(
            select(UnmatchedTonTx).where(UnmatchedTonTx.resolution == "pending").order_by(UnmatchedTonTx.id.desc())
        )
    ).all()
    return [
        {
            "id": r.id,
            "tx_hash": r.tx_hash,
            "amount_ton": str(r.amount_ton),
            "comment": r.comment,
            "sender": r.sender,
            "at": r.created_at.isoformat(),
        }
        for r in rows
    ]


class ResolveUnmatchedIn(BaseModel):
    user_id: int | None = None


@router.post("/finance/unmatched/{row_id}/resolve")
async def resolve_unmatched(
    row_id: int, body: ResolveUnmatchedIn, actor: AdminActor, session: Session
) -> dict[str, str]:
    svc = Services(session)
    row = await AdminService(session, svc.settings).resolve_unmatched(
        actor.id, row_id, body.user_id, await svc.rates.ton_usd()
    )
    return {"resolution": row.resolution}


class ExpenseIn(BaseModel):
    category: ExpenseCategory
    amount_usd: Decimal
    note: str | None = None
    spent_on: date | None = None


@router.get("/expenses")
async def list_expenses(actor: AdminActor, session: Session) -> list[dict[str, Any]]:
    rows = (
        await session.scalars(select(Expense).order_by(Expense.spent_on.desc(), Expense.id.desc()).limit(100))
    ).all()
    return [
        {
            "id": e.id,
            "category": e.category.value,
            "amount_usd": str(e.amount_usd),
            "note": e.note,
            "spent_on": e.spent_on.isoformat(),
        }
        for e in rows
    ]


@router.post("/expenses")
async def add_expense(body: ExpenseIn, actor: AdminActor, session: Session) -> dict[str, bool]:
    await AdminService(session, SettingsService(session)).add_expense(
        actor.id, body.category, body.amount_usd, body.note, body.spent_on
    )
    return {"ok": True}


@router.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: int, actor: AdminActor, session: Session) -> dict[str, bool]:
    e = await session.get(Expense, expense_id)
    if e is None:
        raise NotFound("expense")
    await session.delete(e)
    return {"ok": True}


# ---------- promo ----------
class PromoCreate(BaseModel):
    code: str
    type: PromoType
    value: Decimal
    applies_to: ProductScope = ProductScope.ALL
    max_uses: int | None = None
    per_user_limit: int = 1
    min_order_usd: Decimal | None = None


@router.get("/promo-codes")
async def promo_list(actor: AdminActor, session: Session) -> list[dict[str, Any]]:
    rows = (await session.scalars(select(PromoCode).order_by(PromoCode.id.desc()))).all()
    return [
        {
            "id": p.id,
            "code": p.code,
            "type": p.type.value,
            "value": str(p.value),
            "applies_to": p.applies_to.value,
            "max_uses": p.max_uses,
            "used_count": p.used_count,
            "is_active": p.is_active,
            "valid_to": p.valid_to.isoformat() if p.valid_to else None,
        }
        for p in rows
    ]


@router.post("/promo-codes")
async def promo_create(body: PromoCreate, actor: AdminActor, session: Session) -> dict[str, int]:
    p = await AdminService(session, SettingsService(session)).create_promo(
        actor.id, body.code, body.type, body.value, applies_to=body.applies_to, max_uses=body.max_uses,
        per_user_limit=body.per_user_limit, min_order_usd=body.min_order_usd,
    )  # fmt: skip
    return {"id": p.id}


@router.delete("/promo-codes/{promo_id}")
async def promo_disable(promo_id: int, actor: AdminActor, session: Session) -> dict[str, bool]:
    p = await session.get(PromoCode, promo_id)
    if p is None:
        raise NotFound("promo")
    p.is_active = False
    return {"ok": True}


# ---------- broadcasts ----------
class BroadcastIn(BaseModel):
    content: dict[str, Any]
    segment: dict[str, Any] = {}
    scheduled_at: str | None = None


def _bsvc(session: Session) -> BroadcastService:
    return BroadcastService(session, runtime().messenger)


@router.get("/broadcasts")
async def broadcasts(actor: AdminActor, session: Session) -> list[dict[str, Any]]:
    from app.models import Broadcast

    svc = _bsvc(session)
    rows = (await session.scalars(select(Broadcast).order_by(Broadcast.id.desc()).limit(30))).all()
    return [await svc.progress(b) for b in rows]


@router.post("/broadcasts")
async def broadcast_create(body: BroadcastIn, actor: AdminActor, session: Session) -> dict[str, Any]:
    svc = _bsvc(session)
    b = await svc.create(actor.id, body.content, body.segment)
    if body.scheduled_at:
        from datetime import datetime

        b.scheduled_at, b.status = datetime.fromisoformat(body.scheduled_at), BroadcastStatus.SCHEDULED
    return await svc.progress(b)


@router.post("/broadcasts/{bid}/preview")
async def broadcast_preview(bid: int, actor: AdminActor, session: Session) -> dict[str, bool]:
    svc = _bsvc(session)
    await svc.send_test(await svc.get(bid), actor.id)
    return {"ok": True}


@router.post("/broadcasts/{bid}/{action}")
async def broadcast_action(bid: int, action: str, actor: AdminActor, session: Session) -> dict[str, Any]:
    svc = _bsvc(session)
    b = await svc.get(bid)
    fn = {"start": svc.start, "pause": svc.pause, "cancel": svc.cancel}.get(action)
    if fn is None:
        raise NotFound("action")
    await fn(b)
    from app.services.audit_service import AuditService

    await AuditService(session).log(actor.id, f"broadcast.{action}", "broadcast", bid, source="webapp")
    return await svc.progress(b)


@router.get("/broadcasts/{bid}")
async def broadcast_get(bid: int, actor: AdminActor, session: Session) -> dict[str, Any]:
    svc = _bsvc(session)
    return await svc.progress(await svc.get(bid))


# ---------- channels / admins / audit / health ----------
class ChannelIn(BaseModel):
    chat_id: int
    title: str
    invite_link: str | None = None


@router.get("/channels")
async def channels(actor: AdminActor, session: Session) -> list[dict[str, Any]]:
    rows = (await session.scalars(select(Channel).order_by(Channel.id))).all()
    return [
        {"id": c.id, "chat_id": c.chat_id, "title": c.title, "invite_link": c.invite_link, "is_active": c.is_active}
        for c in rows
    ]


@router.post("/channels")
async def channel_add(body: ChannelIn, actor: AdminActor, session: Session) -> dict[str, bool]:
    await AdminService(session, SettingsService(session)).add_channel(
        actor.id, body.chat_id, body.title, body.invite_link
    )
    return {"ok": True}


@router.delete("/channels/{cid}")
async def channel_del(cid: int, actor: AdminActor, session: Session) -> dict[str, bool]:
    c = await session.get(Channel, cid)
    if c is None:
        raise NotFound("channel")
    await session.delete(c)
    return {"ok": True}


class AdminIn(BaseModel):
    user_id: int
    role: AdminRole


@router.get("/admins")
async def admins_list(actor: OwnerActor, session: Session) -> list[dict[str, Any]]:
    return await AdminService(session, SettingsService(session)).list_admins()


@router.post("/admins")
async def admins_add(body: AdminIn, actor: OwnerActor, session: Session) -> dict[str, bool]:
    await AdminService(session, SettingsService(session)).add_admin(actor.id, body.user_id, body.role)
    return {"ok": True}


@router.delete("/admins/{user_id}")
async def admins_remove(user_id: int, actor: OwnerActor, session: Session) -> dict[str, bool]:
    await AdminService(session, SettingsService(session)).remove_admin(actor.id, user_id)
    return {"ok": True}


@router.get("/audit-logs")
async def audit(
    actor: AdminActor, session: Session, action: str | None = None, limit: int = Query(50, le=200), offset: int = 0
) -> list[dict[str, Any]]:
    stmt = select(AuditLog).order_by(AuditLog.id.desc()).limit(limit).offset(offset)
    if action:
        stmt = stmt.where(AuditLog.action.like(f"{action}%"))
    return [
        {
            "id": a.id,
            "actor_id": a.actor_id,
            "action": a.action,
            "entity": a.entity,
            "entity_id": a.entity_id,
            "before": a.before,
            "after": a.after,
            "source": a.source,
            "at": a.created_at.isoformat(),
        }
        for a in (await session.scalars(stmt)).all()
    ]


@router.get("/health")
async def health(actor: AdminActor, session: Session) -> dict[str, Any]:
    out: dict[str, Any] = {"db": True}
    try:
        await session.execute(select(1))
    except Exception:  # noqa: BLE001
        out["db"] = False
    try:
        out["redis"] = bool(await get_redis().ping())
        hb = await get_redis().get("worker:heartbeat")
        out["worker_heartbeat"] = hb
    except Exception:  # noqa: BLE001
        out["redis"] = False
    out["maintenance"] = bool(await SettingsService(session).get("bot.maintenance"))
    out["payment_methods"] = {
        m.value: bool(await SettingsService(session).get(f"payments.{m.value}.enabled")) for m in PaymentMethod
    }
    return out
