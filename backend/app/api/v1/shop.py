from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Header, Query
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, Session
from app.api.runtime import Services, resolve_recipient, runtime
from app.core.enums import OrderStatus, PaymentMethod, PaymentStatus, ProductType, RecipientType
from app.core.errors import Maintenance, MethodDisabled, NotFound, RateLimited, ValidationFailed
from app.core.money import quantize
from app.core.redis import get_redis
from app.models import Order, Payment, PremiumPlan
from app.services.balance_service import BalanceService
from app.services.catalog_service import CatalogService, quote_dict
from app.services.checkout_service import CreateOrderRequest, normalize_username
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService
from app.services.promo_service import PromoService
from app.services.referral_service import ReferralService

router = APIRouter(tags=["shop"])


# ----- serializers -----
def order_dict(o: Order) -> dict[str, Any]:
    return {
        "public_id": o.public_id,
        "product_type": o.product_type.value,
        "plan_months": o.plan_months,
        "stars_amount": o.stars_amount,
        "recipient_type": o.recipient_type.value,
        "recipient_username": o.recipient_username,
        "recipient_name": o.recipient_name,
        "status": o.status.value,
        "payment_method": o.payment_method.value,
        "price_usd": str(quantize(o.price_usd)),
        "discount_usd": str(quantize(o.discount_usd)),
        "price_amount": str(o.price_amount.normalize()) if o.price_amount is not None else None,
        "price_currency": o.price_currency,
        "error_code": o.error_code,
        "created_at": o.created_at.isoformat(),
        "paid_at": o.paid_at.isoformat() if o.paid_at else None,
        "completed_at": o.completed_at.isoformat() if o.completed_at else None,
    }


def payment_dict(p: Payment) -> dict[str, Any]:
    return {
        "public_id": p.public_id,
        "method": p.method.value,
        "status": p.status.value,
        "amount": str(p.amount.normalize()),
        "currency": p.currency,
        "amount_usd": str(quantize(p.amount_usd)),
        "expires_at": p.expires_at.isoformat() if p.expires_at else None,
        "is_late": p.is_late,
    }


async def rate_limit(user_id: int, bucket: str, limit: int, window: int = 60) -> None:
    redis = get_redis()
    key = f"rl:{bucket}:{user_id}"
    n = await redis.incr(key)
    if n == 1:
        await redis.expire(key, window)
    if n > limit:
        raise RateLimited()


async def ensure_not_maintenance(svc: Services, user_id: int) -> None:
    from app.services.user_service import UserService

    if await svc.settings.get("bot.maintenance") and await UserService(svc.session).role_of(user_id) is None:
        raise Maintenance()


# ----- catalog -----
@router.get("/catalog")
async def catalog(user: CurrentUser, session: Session) -> dict[str, Any]:
    svc = Services(session)
    return await CatalogService(session, svc.settings, svc.pricing, svc.rates).catalog()


class StarsQuoteIn(BaseModel):
    amount: int


@router.post("/catalog/stars-quote")
async def stars_quote(body: StarsQuoteIn, user: CurrentUser, session: Session) -> dict[str, Any]:
    return quote_dict(await Services(session).pricing.quote_stars(body.amount))


class ResolveIn(BaseModel):
    username: str
    product: ProductType = ProductType.PREMIUM
    months: int = 3


@router.post("/recipients/resolve")
async def resolve_recipient_route(body: ResolveIn, user: CurrentUser, session: Session) -> dict[str, Any]:
    await rate_limit(user.id, "resolve", 30)
    username = normalize_username(body.username)
    return await resolve_recipient(Services(session), username, body.product.value, body.months)


class PromoIn(BaseModel):
    code: str
    product_type: ProductType
    plan_id: int | None = None
    stars_amount: int | None = None


@router.post("/promo/validate")
async def promo_validate(body: PromoIn, user: CurrentUser, session: Session) -> dict[str, Any]:
    svc = Services(session)
    if body.product_type == ProductType.PREMIUM:
        plan = await session.get(PremiumPlan, body.plan_id) if body.plan_id else None
        if plan is None:
            raise NotFound("plan")
        base = await svc.pricing.quote_premium(plan)
    else:
        base = await svc.pricing.quote_stars(body.stars_amount or 0)
    promo = await PromoService(session).validate(body.code, user.id, body.product_type, base.price_usd)
    discount = PromoService.discount_for(promo, base.price_usd)
    final = max(base.price_usd - discount, base.min_price_usd)
    return {
        "valid": True,
        "discount_usd": str(quantize(base.price_usd - final)),
        "final_price_usd": str(quantize(final)),
    }


# ----- orders -----
class RecipientIn(BaseModel):
    type: RecipientType = RecipientType.SELF
    username: str | None = None
    user_id: int | None = None
    name: str | None = None


class OrderIn(BaseModel):
    product_type: ProductType
    plan_id: int | None = None
    stars_amount: int | None = Field(default=None, ge=50)
    recipient: RecipientIn = RecipientIn()
    payment_method: PaymentMethod
    promo_code: str | None = None


@router.post("/orders")
async def create_order(
    body: OrderIn, user: CurrentUser, session: Session, idempotency_key: Annotated[str | None, Header()] = None
) -> dict[str, Any]:
    svc = Services(session)
    await ensure_not_maintenance(svc, user.id)
    await rate_limit(user.id, "orders", 10)
    res = await svc.checkout.create_order(
        user,
        CreateOrderRequest(
            product_type=body.product_type,
            payment_method=body.payment_method,
            plan_id=body.plan_id,
            stars_amount=body.stars_amount,
            recipient_type=body.recipient.type,
            recipient_username=body.recipient.username,
            recipient_user_id=None,  # the Mini App cannot prove a user_id; username-based delivery is used
            recipient_name=body.recipient.name,
            promo_code=body.promo_code,
            idempotency_key=idempotency_key,
        ),
    )
    assert res.order is not None
    ins = res.instructions
    return {
        "order": order_dict(res.order),
        "payment_instructions": {"payment_id": ins.payment_id, "method": ins.method, "amount": ins.amount,
                                 "currency": ins.currency, "expires_at": ins.expires_at, **ins.extra},
    }  # fmt: skip


@router.get("/orders")
async def list_orders(
    user: CurrentUser, session: Session, status: str | None = None, limit: int = Query(20, le=50), offset: int = 0
) -> dict[str, Any]:
    wanted: list[OrderStatus] | None = None
    if status == "active":
        wanted = [OrderStatus.AWAITING_PAYMENT, OrderStatus.PAID, OrderStatus.PROCESSING, OrderStatus.NEEDS_REVIEW]
    elif status in {s.value for s in OrderStatus}:
        wanted = [OrderStatus(status)]
    rows = await OrderService(session).list_for_user(user.id, wanted, limit + 1, offset)
    return {"items": [order_dict(o) for o in rows[:limit]], "has_more": len(rows) > limit}


@router.get("/orders/{public_id}")
async def get_order(public_id: str, user: CurrentUser, session: Session) -> dict[str, Any]:
    svc = OrderService(session)
    order = await svc.by_public_id(public_id, user.id)
    events = await svc.events(order.id)
    payments = await session_payments(session, order.id)
    return {
        **order_dict(order),
        "events": [{"status": e.to_status.value, "at": e.created_at.isoformat()} for e in events],
        "payments": [payment_dict(p) for p in payments],
    }


async def session_payments(session: Session, order_id: int) -> list[Payment]:
    from sqlalchemy import select

    return list((await session.scalars(select(Payment).where(Payment.order_id == order_id).order_by(Payment.id))).all())


@router.post("/orders/{public_id}/cancel")
async def cancel_order(public_id: str, user: CurrentUser, session: Session) -> dict[str, Any]:
    svc = Services(session)
    order = await OrderService(session).by_public_id(public_id, user.id)
    return order_dict(await svc.checkout.cancel(order, user.id))


# ----- payments -----
@router.get("/payments/{public_id}")
async def get_payment(public_id: str, user: CurrentUser, session: Session) -> dict[str, Any]:
    svc = Services(session)
    p = await PaymentService(session, svc.settings, svc.notifier).by_public_id(public_id, user.id)
    if p is None:
        raise NotFound("payment")
    return payment_dict(p)


@router.get("/payments/{public_id}/instructions")
async def payment_instructions(public_id: str, user: CurrentUser, session: Session) -> dict[str, Any]:
    svc = Services(session)
    ps = PaymentService(session, svc.settings, svc.notifier)
    p = await ps.by_public_id(public_id, user.id)
    if p is None:
        raise NotFound("payment")
    ins = await ps.instructions(p)
    return {
        "payment_id": ins.payment_id, "method": ins.method, "amount": ins.amount, "currency": ins.currency,
        "expires_at": ins.expires_at, "status": p.status.value, "purpose": p.purpose.value, **ins.extra,
    }  # fmt: skip


class SubmittedIn(BaseModel):
    boc: str | None = None


@router.post("/payments/{public_id}/ton/submitted")
async def ton_submitted(public_id: str, body: SubmittedIn, user: CurrentUser, session: Session) -> dict[str, bool]:
    # The BOC is only a hint to poll sooner; confirmation always comes from the blockchain watcher.
    await get_redis().set(f"ton:hint:{public_id}", "1", ex=600)
    return {"ok": True}


@router.post("/payments/{public_id}/stars-link")
async def stars_link(public_id: str, user: CurrentUser, session: Session) -> dict[str, str]:
    svc = Services(session)
    p = await PaymentService(session, svc.settings, svc.notifier).by_public_id(public_id, user.id)
    if p is None or p.method != PaymentMethod.STARS or p.status != PaymentStatus.PENDING:
        raise NotFound("payment")
    gw = runtime().stars
    if gw is None:
        raise MethodDisabled("stars unavailable")
    title = "Telegram Stars" if p.order_id is None else "Soft-tg-Market"
    link = await gw.create_invoice_link(title, f"#{p.public_id}", p.public_id, int(p.amount))
    return {"invoice_link": link}


# ----- wallet / referral -----
@router.get("/wallet")
async def wallet(user: CurrentUser, session: Session) -> dict[str, Any]:
    svc = Services(session)
    ton, uzs = await svc.rates.ton_usd(), await svc.rates.usd_uzs()
    return {"balance_usd": str(quantize(user.balance_usd)), "balance_uzs": int(user.balance_usd * uzs),
            "balance_ton": str(quantize(user.balance_usd / ton, "0.01"))}  # fmt: skip


@router.get("/wallet/transactions")
async def wallet_tx(
    user: CurrentUser, session: Session, limit: int = Query(20, le=50), offset: int = 0
) -> dict[str, Any]:
    rows = await BalanceService(session).history(user.id, limit + 1, offset)
    return {
        "items": [
            {
                "amount_usd": str(quantize(t.amount_usd)),
                "balance_after": str(quantize(t.balance_after)),
                "type": t.type.value,
                "at": t.created_at.isoformat(),
            }
            for t in rows[:limit]
        ],
        "has_more": len(rows) > limit,
    }


class TopupIn(BaseModel):
    amount_usd: Decimal
    method: PaymentMethod


@router.post("/wallet/topup")
async def topup(body: TopupIn, user: CurrentUser, session: Session) -> dict[str, Any]:
    svc = Services(session)
    await ensure_not_maintenance(svc, user.id)
    await rate_limit(user.id, "topup", 10)
    if body.method == PaymentMethod.BALANCE:
        raise ValidationFailed("method")
    res = await svc.checkout.create_topup(user, body.amount_usd, body.method)
    ins = res.instructions
    return {
        "payment_instructions": {
            "payment_id": ins.payment_id,
            "method": ins.method,
            "amount": ins.amount,
            "currency": ins.currency,
            "expires_at": ins.expires_at,
            **ins.extra,
        }
    }


@router.get("/referral")
async def referral(user: CurrentUser, session: Session) -> dict[str, Any]:
    from app.core.config import get_settings

    svc = Services(session)
    stats = await ReferralService(session, svc.settings, svc.notifier).stats(user.id)
    bot = get_settings().bot_username
    return {
        "link": f"https://t.me/{bot}?start=ref_{user.id}" if bot else None,
        "percent": await svc.settings.get("referral.percent"),
        **stats,
    }
