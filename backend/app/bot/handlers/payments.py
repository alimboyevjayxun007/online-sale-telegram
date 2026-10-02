import structlog
from aiogram import F, Router
from aiogram.types import Message, PreCheckoutQuery

from app.api.runtime import Services
from app.bot.helpers import usd
from app.models import User

log = structlog.get_logger()
router = Router(name="payments")


@router.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery, svc: Services, user: User) -> None:
    ok, reason = await svc.checkout.payments.validate_pre_checkout(
        q.invoice_payload, q.from_user.id, q.total_amount, q.currency
    )
    if ok:
        await q.answer(ok=True)
    else:
        log.warning("pre_checkout_rejected", reason=reason, payload=q.invoice_payload)
        await q.answer(
            ok=False, error_message="⚠️ Payment cannot be processed (expired or changed). Please start again."
        )


@router.message(F.successful_payment)
async def successful_payment(m: Message, svc: Services, user: User) -> None:
    sp = m.successful_payment
    assert sp is not None
    payment = await svc.checkout.payments.handle_successful_stars_payment(
        sp.invoice_payload, user.id, sp.telegram_payment_charge_id, sp.total_amount
    )
    if payment is not None and payment.order_id is None:  # top-up has no order message
        await svc.session.flush()
        await m.answer(f"✅ {usd(payment.amount_usd)}")


@router.message(F.refunded_payment)
async def refunded_payment(m: Message, svc: Services, user: User) -> None:
    rp = m.refunded_payment
    assert rp is not None
    await svc.checkout.payments.record_telegram_refund(user.id, rp.telegram_payment_charge_id, rp.total_amount)
