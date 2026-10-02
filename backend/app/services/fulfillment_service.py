from datetime import timedelta
from decimal import Decimal

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    BalanceTxType,
    Direction,
    HotWalletTxKind,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    ProductType,
    ProviderCode,
    StarsTxKind,
)
from app.core.errors import InvalidState, ProviderUnavailable, ProviderUncertain, RecipientInvalid
from app.core.money import D, quantize
from app.core.timeutil import now_utc
from app.i18n import t
from app.models import HotWalletTransaction, Order, Payment, StarsTransaction, User
from app.providers.fulfillment.base import DeliveryResult, FulfillmentProvider
from app.providers.fulfillment.bot_stars import GIFT_STARS
from app.providers.fulfillment.gateway import StarsGateway
from app.services.balance_service import BalanceService
from app.services.notification_service import NotificationService
from app.services.order_service import OrderService
from app.services.rate_service import RateService
from app.services.referral_service import ReferralService
from app.services.settings_service import SettingsService

log = structlog.get_logger()
BACKOFF = [timedelta(seconds=30), timedelta(minutes=2), timedelta(minutes=10)]
STUCK_AFTER = timedelta(minutes=10)


class FulfillmentService:
    def __init__(
        self,
        session: AsyncSession,
        settings: SettingsService,
        rates: RateService,
        providers: dict[ProviderCode, FulfillmentProvider],
        notifier: NotificationService,
        stars: StarsGateway | None = None,
    ) -> None:
        self.session, self.settings, self.rates = session, settings, rates
        self.providers, self.notifier, self.stars = providers, notifier, stars
        self.orders = OrderService(session)
        self.balance = BalanceService(session)
        self.referral = ReferralService(session, settings, notifier)

    # ---------- queue ----------
    async def claim_next(self) -> Order | None:
        """Atomically take the oldest due 'paid' order (SKIP LOCKED) and mark it 'processing'."""
        now = now_utc()
        order = await self.session.scalar(
            select(Order)
            .where(Order.status == OrderStatus.PAID, (Order.next_attempt_at.is_(None)) | (Order.next_attempt_at <= now))
            .order_by(Order.paid_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if order is None:
            return None
        await self.orders.transition(
            order, OrderStatus.PROCESSING, "worker", attempts=order.attempts + 1, locked_at=now
        )
        await self.session.commit()
        return order

    async def process_next(self) -> bool:
        order = await self.claim_next()
        if order is None:
            return False
        await self.process_order(order)
        await self.session.commit()
        return True

    # ---------- provider selection ----------
    async def select_providers(self, order: Order) -> list[FulfillmentProvider]:
        priority = [ProviderCode(c) for c in await self.settings.get("fulfillment.premium.priority")]
        if order.product_type == ProductType.STARS:
            priority = [c for c in priority if c != ProviderCode.BOT_STARS]
        elif (
            order.payment_method == PaymentMethod.STARS
            and await self.settings.get("fulfillment.stars_paid_strategy") == "bot_stars"
        ):
            priority = [ProviderCode.BOT_STARS] + [c for c in priority if c != ProviderCode.BOT_STARS]
        out: list[FulfillmentProvider] = []
        star_rate = D(await self.settings.get("pricing.star_usd_rate"))
        for code in priority:
            p = self.providers.get(code)
            if p is None or not await p.supports(order) or not await p.is_available():
                continue
            if code == ProviderCode.BOT_STARS and order.payment_method != PaymentMethod.STARS:
                # fallback paid out of the bot's Stars: never sell at a loss automatically
                if D(GIFT_STARS.get(order.plan_months or 0, 0)) * star_rate > order.price_usd:
                    log.warning("bot_stars_fallback_skipped_unprofitable", order=order.public_id)
                    continue
            out.append(p)
        if not out and ProviderCode.MOCK in self.providers:
            out.append(self.providers[ProviderCode.MOCK])
        return out

    # ---------- processing ----------
    async def process_order(self, order: Order) -> None:
        user = await self.session.get(User, order.user_id)
        assert user is not None
        providers = await self.select_providers(order)
        if not providers:
            await self._temporary_failure(order, user, "no_provider")
            return
        for provider in providers:
            try:
                result = await provider.deliver(order)
            except ProviderUnavailable as exc:
                log.warning("provider_unavailable", provider=provider.code.value, order=order.public_id, error=str(exc))
                continue
            except RecipientInvalid as exc:
                await self._fail(order, user, "recipient_invalid", str(exc))
                return
            except ProviderUncertain as exc:
                await self._needs_review(order, user, provider.code, str(exc))
                return
            await self._complete(order, user, provider.code, result)
            return
        await self._temporary_failure(order, user, "providers_unavailable")

    async def _temporary_failure(self, order: Order, user: User, code: str) -> None:
        max_attempts = int(await self.settings.get("fulfillment.max_attempts"))
        if order.attempts >= max_attempts:
            await self._fail(order, user, code, "max attempts reached")
            return
        delay = BACKOFF[min(order.attempts - 1, len(BACKOFF) - 1)]
        await self.orders.transition(
            order, OrderStatus.PAID, "worker", error_code=code, next_attempt_at=now_utc() + delay
        )

    async def _complete(self, order: Order, user: User, provider: ProviderCode, result: DeliveryResult) -> None:
        ton_usd = await self.rates.ton_usd()
        star_rate = D(await self.settings.get("pricing.star_usd_rate"))
        cost_usd = result.cost_amount * ton_usd if result.cost_currency == "TON" else result.cost_amount * star_rate
        cost_usd = quantize(cost_usd + result.network_fee_ton * ton_usd)
        if result.cost_currency == "TON":
            self.session.add(
                HotWalletTransaction(
                    direction=Direction.OUT,
                    kind=HotWalletTxKind.FULFILLMENT,
                    amount_ton=result.cost_amount,
                    fee_ton=result.network_fee_ton,
                    amount_usd=cost_usd,
                    rate_used=ton_usd,
                    tx_hash=result.provider_ref if len(result.provider_ref) == 64 else None,
                    order_id=order.id,
                )
            )
        else:
            self.session.add(
                StarsTransaction(
                    direction=Direction.OUT,
                    kind=StarsTxKind.PREMIUM_GIFT,
                    amount=int(result.cost_amount),
                    order_id=order.id,
                )
            )
        await self.orders.transition(
            order,
            OrderStatus.COMPLETED,
            "worker",
            provider=provider,
            provider_ref=result.provider_ref,
            cost_usd=cost_usd,
            cost_amount=result.cost_amount,
            cost_currency=result.cost_currency,
            profit_usd=quantize(order.price_usd - cost_usd),
            completed_at=now_utc(),
            error_code=None,
            locked_at=None,
        )
        user.orders_count += 1
        user.total_spent_usd = quantize(user.total_spent_usd + order.price_usd)
        await self.referral.reward_for_order(order)
        who = (
            t(user.language, "who_self")
            if order.recipient_type.value == "self"
            else f"@{order.recipient_username or order.recipient_user_id}"
        )
        if order.product_type == ProductType.PREMIUM:
            what = t(user.language, "what_premium", who=who, months=order.plan_months)
        else:
            what = t(user.language, "what_stars", who=who, amount=order.stars_amount)
        paid = f"{order.price_amount:f} {order.price_currency}" if order.price_amount else f"{order.price_usd} $"
        await self.notifier.notify_order(order, user, "order_completed", what=what, oid=order.public_id, paid=paid)
        if (
            order.recipient_type.value == "other"
            and order.recipient_user_id
            and order.product_type == ProductType.PREMIUM
        ):
            target = await self.session.get(User, order.recipient_user_id)
            if target is not None:
                await self.notifier.notify_user(
                    target,
                    "gift_received",
                    who=f"@{user.username}" if user.username else user.first_name or "",
                    months=order.plan_months,
                )
        await self.notifier.alert(
            f"✅ {order.public_id} · {order.product_type.value} · {order.price_usd}$ · foyda {order.profit_usd}$ · {provider.value}",
            event="order_completed",
        )

    async def _fail(self, order: Order, user: User, code: str, message: str) -> None:
        await self.orders.transition(
            order, OrderStatus.FAILED, "worker", error_code=code, error_message=message[:500], locked_at=None
        )
        await self.notifier.alert(
            f"❌ {order.public_id} bajarilmadi: {code} ({message[:100]})", "warn", event="order_failed"
        )
        if await self.settings.get("fulfillment.auto_refund"):
            await self.refund(order, "system")

    async def _needs_review(self, order: Order, user: User, provider: ProviderCode, message: str) -> None:
        await self.orders.transition(
            order,
            OrderStatus.NEEDS_REVIEW,
            "worker",
            provider=provider,
            error_code="uncertain",
            error_message=message[:500],
        )
        await self.notifier.notify_order(order, user, "order_review", oid=order.public_id)
        await self.notifier.alert(
            f"🔍 {order.public_id} tekshirish kerak: natija noaniq ({provider.value}). Avtomatik qaytarilmaydi.", "crit"
        )

    # ---------- refunds / admin actions ----------
    async def refund(self, order: Order, actor: str, to: str = "auto") -> Order:
        if order.status not in (OrderStatus.FAILED, OrderStatus.NEEDS_REVIEW, OrderStatus.PAID):
            raise InvalidState(f"cannot refund {order.status.value}")
        user = await self.session.get(User, order.user_id)
        assert user is not None
        payment = await self.session.scalar(
            select(Payment)
            .where(Payment.order_id == order.id, Payment.status == PaymentStatus.CONFIRMED)
            .order_by(Payment.id.desc())
        )
        refunded_stars = False
        if (
            payment is not None
            and payment.method == PaymentMethod.STARS
            and to in ("auto", "stars")
            and self.stars is not None
            and payment.tg_charge_id
        ):
            try:
                await self.stars.refund_star_payment(user.id, payment.tg_charge_id)
                payment.status = PaymentStatus.REFUNDED
                self.session.add(
                    StarsTransaction(
                        direction=Direction.OUT,
                        kind=StarsTxKind.REFUND,
                        amount=int(payment.amount),
                        order_id=order.id,
                        payment_id=payment.id,
                        tg_charge_id=payment.tg_charge_id,
                    )
                )
                refunded_stars = True
            except Exception as exc:  # noqa: BLE001 - fall back to balance credit
                log.warning("stars_refund_failed", order=order.public_id, error=str(exc))
        if refunded_stars:
            assert payment is not None
            note = t(user.language, "refund_stars", amount=int(payment.amount))
        else:
            await self.balance.credit(
                user.id, order.price_usd, BalanceTxType.REFUND, "order", order.id, created_by=None
            )
            note = t(user.language, "refund_balance", amount=f"{order.price_usd:.2f} $")
        await self.referral.revoke_for_order(order)
        await self.orders.transition(order, OrderStatus.REFUNDED, actor, locked_at=None)
        await self.notifier.notify_order(order, user, "order_failed", oid=order.public_id, refund=note)
        return order

    async def retry(self, order: Order, actor: str) -> Order:
        if order.status not in (OrderStatus.FAILED, OrderStatus.NEEDS_REVIEW):
            raise InvalidState("only failed/needs_review orders can be retried")
        return await self.orders.transition(
            order, OrderStatus.PAID, actor, attempts=0, next_attempt_at=None, error_code=None
        )

    async def mark_completed_manually(self, order: Order, actor: str, provider_ref: str = "manual") -> Order:
        if order.status not in (OrderStatus.NEEDS_REVIEW, OrderStatus.FAILED):
            raise InvalidState("only failed/needs_review orders can be completed manually")
        user = await self.session.get(User, order.user_id)
        assert user is not None
        await self._complete(order, user, ProviderCode.MANUAL, DeliveryResult(provider_ref, Decimal(0), "TON"))
        return order

    async def recover_stuck(self) -> int:
        """Orders stuck in 'processing' (worker died) are NOT retried automatically: money may have moved."""
        cutoff = now_utc() - STUCK_AFTER
        stuck = (
            await self.session.scalars(
                select(Order)
                .where(Order.status == OrderStatus.PROCESSING, Order.locked_at < cutoff)
                .with_for_update(skip_locked=True)
            )
        ).all()
        for order in stuck:
            user = await self.session.get(User, order.user_id)
            assert user is not None
            await self._needs_review(order, user, order.provider or ProviderCode.MANUAL, "stuck in processing")
        return len(stuck)
