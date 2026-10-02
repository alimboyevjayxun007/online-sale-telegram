import re
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    BalanceTxType,
    OrderStatus,
    PaymentMethod,
    PaymentPurpose,
    PaymentStatus,
    ProductType,
    RecipientType,
)
from app.core.errors import MethodDisabled, NotFound, PlanUnavailable, ValidationFailed
from app.core.ids import public_id
from app.models import Order, Payment, PremiumPlan, PromoCode, User
from app.services.balance_service import BalanceService
from app.services.notification_service import NotificationService
from app.services.order_service import OrderService
from app.services.payment_service import PaymentInstructions, PaymentService
from app.services.pricing_service import PricingService, Quote
from app.services.promo_service import PromoService
from app.services.settings_service import SettingsService

USERNAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{4,31}$")


def normalize_username(raw: str) -> str:
    name = raw.strip().lstrip("@")
    if "t.me/" in name:
        name = name.split("t.me/")[-1].split("?")[0].strip("/")
    if not USERNAME_RE.match(name):
        raise ValidationFailed("invalid username")
    return name


@dataclass
class CreateOrderRequest:
    product_type: ProductType
    payment_method: PaymentMethod
    plan_id: int | None = None
    stars_amount: int | None = None
    recipient_type: RecipientType = RecipientType.SELF
    recipient_username: str | None = None
    recipient_user_id: int | None = None
    recipient_name: str | None = None
    promo_code: str | None = None
    idempotency_key: str | None = None


@dataclass
class CheckoutResult:
    order: Order | None
    payment: Payment
    instructions: PaymentInstructions
    quote: Quote | None = None


class CheckoutService:
    def __init__(
        self,
        session: AsyncSession,
        settings: SettingsService,
        pricing: PricingService,
        notifier: NotificationService,
    ) -> None:
        self.session, self.settings, self.pricing = session, settings, pricing
        self.orders = OrderService(session)
        self.payments = PaymentService(session, settings, notifier)
        self.promo = PromoService(session)
        self.balance = BalanceService(session)

    async def _check_method(self, method: PaymentMethod, product: ProductType) -> None:
        if method == PaymentMethod.STARS and product == ProductType.STARS:
            raise MethodDisabled("stars cannot buy stars")
        if not await self.settings.get(f"payments.{method.value}.enabled"):
            raise MethodDisabled(method.value)

    async def create_order(self, user: User, req: CreateOrderRequest) -> CheckoutResult:
        if req.idempotency_key:
            existing = await self.session.scalar(
                select(Order).where(Order.user_id == user.id, Order.idempotency_key == req.idempotency_key)
            )
            if existing is not None:
                pay = await self.session.scalar(
                    select(Payment).where(Payment.order_id == existing.id).order_by(Payment.id.desc())
                )
                assert pay is not None
                return CheckoutResult(existing, pay, await self.payments.instructions(pay))
        await self._check_method(req.payment_method, req.product_type)

        # recipient
        if req.recipient_type == RecipientType.SELF:
            rec_user_id: int | None = user.id
            rec_username, rec_name = user.username, user.first_name
        else:
            rec_user_id, rec_name = req.recipient_user_id, req.recipient_name
            rec_username = normalize_username(req.recipient_username) if req.recipient_username else None
            if not rec_username and not rec_user_id:
                raise ValidationFailed("recipient required")
        if req.product_type == ProductType.STARS and not rec_username:
            raise ValidationFailed("stars need a username")

        # price (promo validated against the undiscounted price)
        plan: PremiumPlan | None = None
        if req.product_type == ProductType.PREMIUM:
            plan = await self.session.get(PremiumPlan, req.plan_id) if req.plan_id else None
            if plan is None:
                raise NotFound("plan")
            base = await self.pricing.quote_premium(plan)
        else:
            if not req.stars_amount:
                raise ValidationFailed("stars_amount required")
            base = await self.pricing.quote_stars(req.stars_amount)
        promo: PromoCode | None = None
        if req.promo_code:
            promo = await self.promo.validate(req.promo_code, user.id, req.product_type, base.price_usd, lock=True)
        quote = (
            (
                await self.pricing.quote_premium(plan, promo)
                if plan
                else await self.pricing.quote_stars(req.stars_amount or 0, promo)
            )
            if promo
            else base
        )
        if req.payment_method == PaymentMethod.STARS and quote.price_xtr <= 0:
            raise MethodDisabled("stars")

        amount, currency = quote.amount_for(req.payment_method)
        order = Order(
            public_id=public_id("PR" if plan else "ST"),
            user_id=user.id,
            product_type=req.product_type,
            plan_id=plan.id if plan else None,
            plan_months=plan.months if plan else None,
            stars_amount=req.stars_amount if not plan else None,
            recipient_type=req.recipient_type,
            recipient_username=rec_username,
            recipient_user_id=rec_user_id,
            recipient_name=rec_name,
            status=OrderStatus.AWAITING_PAYMENT,
            payment_method=req.payment_method,
            price_usd=quote.price_usd,
            discount_usd=quote.discount_usd,
            price_amount=amount,
            price_currency=currency,
            idempotency_key=req.idempotency_key,
            meta={"ton_usd": str(quote.ton_usd), "usd_uzs": str(quote.usd_uzs)},
        )
        self.session.add(order)
        await self.session.flush()
        if promo is not None:
            await self.promo.redeem(promo, user.id, order.id, quote.discount_usd)

        payment = await self.payments.create_for(user, req.payment_method, quote, PaymentPurpose.ORDER, order)
        if req.payment_method == PaymentMethod.BALANCE:
            await self.balance.debit(user.id, quote.price_usd, BalanceTxType.PURCHASE, "order", order.id)
            await self.payments.confirm(payment, quote.price_usd, actor=f"user:{user.id}")
            await self.session.refresh(order)
        return CheckoutResult(order, payment, await self.payments.instructions(payment), quote)

    async def create_topup(self, user: User, amount_usd: Decimal, method: PaymentMethod) -> CheckoutResult:
        if method == PaymentMethod.BALANCE:
            raise MethodDisabled("balance")
        if method == PaymentMethod.STARS and not await self.settings.get("payments.topup.stars.enabled"):
            raise MethodDisabled("stars")
        if not await self.settings.get(f"payments.{method.value}.enabled"):
            raise MethodDisabled(method.value)
        quote = await self.pricing.quote_topup(amount_usd)
        payment = await self.payments.create_for(user, method, quote, PaymentPurpose.TOPUP)
        return CheckoutResult(None, payment, await self.payments.instructions(payment), quote)

    async def cancel(self, order: Order, user_id: int) -> Order:
        if order.user_id != user_id:
            raise NotFound("order")
        order = await self.orders.transition(order, OrderStatus.CANCELLED, f"user:{user_id}")
        pays = await self.session.scalars(
            select(Payment).where(Payment.order_id == order.id, Payment.status == PaymentStatus.PENDING)
        )
        for p in pays.all():
            p.status = PaymentStatus.EXPIRED
        return order


__all__ = ["CheckoutService", "CreateOrderRequest", "CheckoutResult", "PlanUnavailable"]
