import secrets
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    BalanceTxType,
    Direction,
    HotWalletTxKind,
    OrderStatus,
    PaymentMethod,
    PaymentPurpose,
    PaymentStatus,
    StarsTxKind,
)
from app.core.ids import ALPHABET, public_id
from app.core.money import D, quantize, to_nano
from app.core.timeutil import now_utc
from app.models import HotWalletTransaction, Order, Payment, StarsTransaction, UnmatchedTonTx, User
from app.providers.ton.chain import IncomingTx
from app.services.balance_service import BalanceService
from app.services.notification_service import NotificationService
from app.services.order_service import OrderService
from app.services.pricing_service import Quote
from app.services.settings_service import SettingsService

log = structlog.get_logger()
TON_TOLERANCE = Decimal("0.001")  # wallets may round amounts slightly
OVERPAY_THRESHOLD = Decimal("0.01")


@dataclass
class PaymentInstructions:
    payment_id: str
    method: str
    amount: str
    currency: str
    expires_at: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def _comment(prefix: str) -> str:
    return f"{prefix}-" + "".join(secrets.choice(ALPHABET) for _ in range(6))


class PaymentService:
    def __init__(
        self,
        session: AsyncSession,
        settings: SettingsService,
        notifier: NotificationService,
    ) -> None:
        self.session = session
        self.settings = settings
        self.notifier = notifier
        self.balance = BalanceService(session)
        self.orders = OrderService(session)

    # ---------- creation ----------
    async def create_for(
        self,
        user: User,
        method: PaymentMethod,
        quote: Quote,
        purpose: PaymentPurpose,
        order: Order | None = None,
    ) -> Payment:
        amount, currency = quote.amount_for(method)
        ttl = int(await self.settings.get("payments.invoice_ttl_minutes"))
        payment = Payment(
            public_id=public_id("TP" if purpose == PaymentPurpose.TOPUP else "PM"),
            user_id=user.id,
            order_id=order.id if order else None,
            purpose=purpose,
            method=method,
            status=PaymentStatus.PENDING,
            amount=amount,
            currency=currency,
            amount_usd=quote.price_usd,
            rate_used=quote.ton_usd,
            expires_at=now_utc() + timedelta(minutes=ttl) if method != PaymentMethod.BALANCE else None,
        )
        if method == PaymentMethod.TON:
            payment.ton_comment = _comment("TP" if purpose == PaymentPurpose.TOPUP else "PM")
        for _ in range(5):
            try:
                async with self.session.begin_nested():
                    self.session.add(payment)
                    await self.session.flush()
                return payment
            except IntegrityError:
                self.session.expunge(payment)
                payment.public_id = public_id("TP" if purpose == PaymentPurpose.TOPUP else "PM")
                if method == PaymentMethod.TON:
                    payment.ton_comment = _comment("TP" if purpose == PaymentPurpose.TOPUP else "PM")
        raise RuntimeError("could not allocate payment ids")

    async def instructions(self, payment: Payment) -> PaymentInstructions:
        base = PaymentInstructions(
            payment.public_id,
            payment.method.value,
            str(payment.amount.normalize() if payment.currency != "XTR" else int(payment.amount)),
            payment.currency,
            payment.expires_at.isoformat() if payment.expires_at else None,
        )
        if payment.method == PaymentMethod.TON:
            address = await self.settings.get("hot_wallet.address")
            nano = to_nano(payment.amount)
            base.extra = {
                "address": address,
                "amount_nano": str(nano),
                "comment": payment.ton_comment,
                "tonkeeper_link": f"https://app.tonkeeper.com/transfer/{address}?amount={nano}&text={payment.ton_comment}",
            }
        return base

    async def by_public_id(self, pid: str, user_id: int | None = None) -> Payment | None:
        stmt = select(Payment).where(Payment.public_id == pid.upper())
        if user_id is not None:
            stmt = stmt.where(Payment.user_id == user_id)
        return await self.session.scalar(stmt)

    # ---------- confirmation ----------
    async def _lock(self, payment_id: int) -> Payment:
        return (await self.session.scalars(select(Payment).where(Payment.id == payment_id).with_for_update())).one()

    async def confirm(self, payment: Payment, received: Decimal | None = None, actor: str = "system") -> Payment:
        """Mark confirmed (idempotent) and trigger the purpose-specific effect."""
        payment = await self._lock(payment.id)
        if payment.status == PaymentStatus.CONFIRMED:
            return payment
        payment.status = PaymentStatus.CONFIRMED
        payment.confirmed_at = now_utc()
        payment.received_amount = received if received is not None else payment.amount
        user = await self.session.get(User, payment.user_id)
        assert user is not None
        if payment.purpose == PaymentPurpose.TOPUP:
            await self.balance.credit(user.id, payment.amount_usd, BalanceTxType.TOPUP, "payment", payment.id)
            await self.notifier.notify_user(user, "balance_topped", amount=f"{payment.amount_usd:.2f} $")
        else:
            assert payment.order_id is not None
            order = await self.orders.get(payment.order_id)
            if payment.method == PaymentMethod.STARS:
                self.session.add(
                    StarsTransaction(
                        direction=Direction.IN,
                        kind=StarsTxKind.PAYMENT_IN,
                        amount=int(payment.amount),
                        order_id=order.id,
                        payment_id=payment.id,
                        tg_charge_id=payment.tg_charge_id,
                    )
                )
            if order.status == OrderStatus.AWAITING_PAYMENT:
                await self.orders.mark_paid(order, actor)
                await self.notifier.notify_order(order, user, "pay_confirmed")
        await self.session.flush()
        return payment

    # ---------- Stars ----------
    async def validate_pre_checkout(self, payload: str, user_id: int, total: int, currency: str) -> tuple[bool, str]:
        payment = await self.by_public_id(payload, user_id)
        if payment is None or payment.method != PaymentMethod.STARS:
            return False, "payment_not_found"
        if payment.status != PaymentStatus.PENDING:
            return False, "payment_not_pending"
        if currency != "XTR" or total != int(payment.amount):
            return False, "amount_mismatch"
        if payment.expires_at and payment.expires_at < now_utc():
            return False, "expired"
        if payment.order_id:
            order = await self.orders.get(payment.order_id)
            if order.status != OrderStatus.AWAITING_PAYMENT:
                return False, "order_closed"
        return True, ""

    async def handle_successful_stars_payment(
        self, payload: str, user_id: int, charge_id: str, total: int
    ) -> Payment | None:
        dup = await self.session.scalar(select(Payment).where(Payment.tg_charge_id == charge_id))
        if dup is not None:
            return dup  # Telegram redelivered the update
        payment = await self.by_public_id(payload, user_id)
        if payment is None or payment.method != PaymentMethod.STARS:
            log.error("stars_payment_unknown", payload=payload, charge_id=charge_id)
            await self.notifier.alert(
                f"Noma'lum Stars to'lovi: payload={payload}, user={user_id}, {total} ⭐, charge={charge_id}", "crit"
            )
            return None
        payment.tg_charge_id = charge_id
        await self.session.flush()
        return await self.confirm(payment, Decimal(total))

    async def record_telegram_refund(self, user_id: int, charge_id: str, total: int) -> None:
        payment = await self.session.scalar(select(Payment).where(Payment.tg_charge_id == charge_id))
        if payment is not None:
            payment.status = PaymentStatus.REFUNDED
        self.session.add(
            StarsTransaction(
                direction=Direction.OUT, kind=StarsTxKind.TELEGRAM_REFUND, amount=total, tg_charge_id=charge_id
            )
        )
        await self.notifier.alert(f"Telegram {total} ⭐ to'lovni qaytardi (user {user_id}, charge {charge_id})", "warn")

    # ---------- TON ----------
    async def process_incoming(self, tx: IncomingTx) -> str:
        """Match a hot-wallet incoming transfer to a payment. Idempotent on tx hash."""
        if not tx.success:
            return "failed_tx"
        rate = await self.session.execute(
            insert(HotWalletTransaction)
            .values(
                direction=Direction.IN,
                kind=HotWalletTxKind.USER_PAYMENT,
                amount_ton=tx.amount_ton,
                tx_hash=tx.hash,
                counterparty=tx.sender,
            )
            .on_conflict_do_nothing(index_elements=["tx_hash"])
            .returning(HotWalletTransaction.id)
        )
        hw_id = rate.scalar_one_or_none()
        if hw_id is None:
            return "duplicate"
        comment = (tx.comment or "").strip().upper()
        payment = (
            await self.session.scalar(select(Payment).where(Payment.ton_comment == comment).with_for_update())
            if comment
            else None
        )
        if payment is None or payment.status in (PaymentStatus.CONFIRMED, PaymentStatus.REFUNDED):
            await self._unmatched(tx)
            return "unmatched"
        await self.session.execute(
            update(HotWalletTransaction)
            .where(HotWalletTransaction.id == hw_id)
            .values(payment_id=payment.id, order_id=payment.order_id)
        )
        user = await self.session.get(User, payment.user_id)
        assert user is not None
        rate_used = payment.rate_used or D(1)
        payment.ton_tx_hash, payment.ton_sender = tx.hash, tx.sender
        received = tx.amount_ton

        def usd(ton: Decimal) -> Decimal:
            return quantize(ton * rate_used)

        if payment.status == PaymentStatus.EXPIRED or (
            payment.expires_at
            and payment.expires_at < now_utc() - timedelta(minutes=2)
            and payment.status == PaymentStatus.PENDING
        ):
            payment.is_late, payment.status, payment.received_amount = True, PaymentStatus.EXPIRED, received
            await self.balance.credit(user.id, usd(received), BalanceTxType.LATE_PAYMENT, "payment", payment.id)
            await self.notifier.notify_user(
                user, "balance_credit_note", amount=f"{usd(received):.2f} $", reason=_reason(user, "reason_late")
            )
            return "late"
        if received + TON_TOLERANCE < payment.amount:
            payment.status, payment.received_amount = PaymentStatus.FAILED, received
            await self.balance.credit(user.id, usd(received), BalanceTxType.UNDERPAYMENT, "payment", payment.id)
            need = f"{payment.amount - received:.2f} TON"
            await self.notifier.notify_user(
                user,
                "balance_credit_note",
                amount=f"{usd(received):.2f} $",
                reason=_reason(user, "reason_under", need=need),
            )
            return "underpaid"
        await self.confirm(payment, received)
        extra = received - payment.amount
        if extra > OVERPAY_THRESHOLD:
            await self.balance.credit(user.id, usd(extra), BalanceTxType.OVERPAYMENT, "payment", payment.id)
            await self.notifier.notify_user(
                user, "balance_credit_note", amount=f"{usd(extra):.2f} $", reason=_reason(user, "reason_over")
            )
        return "confirmed"

    async def _unmatched(self, tx: IncomingTx) -> None:
        await self.session.execute(
            insert(UnmatchedTonTx)
            .values(tx_hash=tx.hash, amount_ton=tx.amount_ton, comment=(tx.comment or "")[:255], sender=tx.sender)
            .on_conflict_do_nothing(index_elements=["tx_hash"])
        )
        await self.notifier.alert(
            f"❓ Mos kelmagan TON to'lov: {tx.amount_ton} TON, izoh: <code>{(tx.comment or '-')[:60]}</code>", "warn"
        )

    # ---------- expiry ----------
    async def expire_stale(self) -> int:
        """Expire pending payments past their deadline; close awaiting orders. Returns #payments expired."""
        now = now_utc()
        pays = (
            await self.session.scalars(
                select(Payment)
                .where(Payment.status == PaymentStatus.PENDING, Payment.expires_at < now)
                .with_for_update(skip_locked=True)
            )
        ).all()
        for p in pays:
            p.status = PaymentStatus.EXPIRED
            if p.order_id:
                order = await self.orders.get(p.order_id)
                if order.status == OrderStatus.AWAITING_PAYMENT:
                    others = await self.session.scalar(
                        select(Payment.id).where(
                            Payment.order_id == order.id, Payment.status == PaymentStatus.PENDING, Payment.id != p.id
                        )
                    )
                    if others is None:
                        await self.orders.transition(order, OrderStatus.EXPIRED, "system")
        await self.session.flush()
        return len(pays)


def _reason(user: User, key: str, **kw: Any) -> str:
    from app.i18n import t

    return t(user.language, key, **kw)
