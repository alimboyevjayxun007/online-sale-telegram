from datetime import timedelta
from decimal import Decimal as Dc

import pytest
from sqlalchemy import func, select

from app.core.enums import (
    OrderStatus as S,
    PaymentMethod as M,
    PaymentStatus,
    ProductType,
    ProviderCode,
    RecipientType,
)
from app.core.errors import InvalidState, MethodDisabled, ValidationFailed
from app.core.timeutil import now_utc
from app.models import (
    BalanceTransaction,
    HotWalletTransaction,
    Order,
    Payment,
    ReferralReward,
    StarsTransaction,
    UnmatchedTonTx,
    User,
)
from app.providers.ton.chain import IncomingTx
from app.services.checkout_service import CreateOrderRequest
from tests.factories import make_user
from tests.helpers import Env, fund, plan_id, seed


@pytest.fixture
async def env(session):
    await seed(session)
    return Env(session)


def premium_req(pid, method, **kw):
    return CreateOrderRequest(ProductType.PREMIUM, method, plan_id=pid, **kw)


async def test_balance_purchase_full_cycle_with_referral(session, env):
    ref = await make_user(session, 1)
    buyer = await make_user(session, 2, referrer_id=1)
    await fund(session, buyer, 50)
    res = await env.checkout.create_order(buyer, premium_req(await plan_id(session, 12), M.BALANCE))
    assert res.order.status == S.PAID and res.payment.status == PaymentStatus.CONFIRMED
    assert buyer.balance_usd == Dc("50") - res.order.price_usd
    assert await env.fulfillment().process_next() is True
    await session.refresh(res.order)
    o = res.order
    assert o.status == S.COMPLETED and o.provider == ProviderCode.MOCK
    assert o.profit_usd == o.price_usd - o.cost_usd and o.cost_usd > 0
    assert buyer.orders_count == 1 and buyer.total_spent_usd == o.price_usd
    reward = await session.scalar(select(ReferralReward))
    assert reward.amount_usd == (o.price_usd * 2 / 100).quantize(Dc("0.000001"))
    await session.refresh(ref)
    assert ref.balance_usd == reward.amount_usd
    assert any("Tayyor" in t for t in env.messenger.texts(2))
    assert await env.fulfillment().process_next() is False  # nothing left


async def test_insufficient_balance_creates_nothing_paid(session, env):
    from app.core.errors import InsufficientBalance

    u = await make_user(session, 2)
    with pytest.raises(InsufficientBalance):
        await env.checkout.create_order(u, premium_req(await plan_id(session, 3), M.BALANCE))


async def test_ton_payment_exact_dup_and_fulfill(session, env):
    await env.settings.set("hot_wallet.address", "UQHot")
    u = await make_user(session, 2)
    res = await env.checkout.create_order(u, premium_req(await plan_id(session, 3), M.TON))
    ins = res.instructions
    assert ins.extra["address"] == "UQHot" and ins.extra["comment"].startswith("PM-")
    assert res.order.status == S.AWAITING_PAYMENT
    tx = IncomingTx("a" * 64, 1, res.payment.amount, ins.extra["comment"], "UQsender")
    assert await env.checkout.payments.process_incoming(tx) == "confirmed"
    assert await env.checkout.payments.process_incoming(tx) == "duplicate"
    await session.refresh(res.order)
    assert res.order.status == S.PAID
    assert (await session.scalar(select(func.count()).select_from(HotWalletTransaction))) == 1
    await env.fulfillment().process_next()
    await session.refresh(res.order)
    assert res.order.status == S.COMPLETED


async def test_ton_underpaid_overpaid_late_unmatched(session, env):
    u = await make_user(session, 2)
    pid = await plan_id(session, 3)
    pay = env.checkout.payments

    r1 = await env.checkout.create_order(u, premium_req(pid, M.TON))
    short = IncomingTx("b" * 64, 2, r1.payment.amount - Dc("1"), r1.instructions.extra["comment"], "s")
    assert await pay.process_incoming(short) == "underpaid"
    await session.refresh(u)
    assert u.balance_usd == ((r1.payment.amount - 1) * r1.payment.rate_used).quantize(Dc("0.000001"))
    await session.refresh(r1.order)
    assert r1.order.status == S.AWAITING_PAYMENT

    r2 = await env.checkout.create_order(u, premium_req(pid, M.TON))
    over = IncomingTx("c" * 64, 3, r2.payment.amount + Dc("0.5"), r2.instructions.extra["comment"], "s")
    before = u.balance_usd
    assert await pay.process_incoming(over) == "confirmed"
    await session.refresh(u)
    assert u.balance_usd - before == (Dc("0.5") * r2.payment.rate_used).quantize(Dc("0.000001"))

    r3 = await env.checkout.create_order(u, premium_req(pid, M.TON))
    r3.payment.expires_at = now_utc() - timedelta(minutes=30)
    r3.payment.status = PaymentStatus.EXPIRED
    await session.flush()
    late = IncomingTx("d" * 64, 4, r3.payment.amount, r3.instructions.extra["comment"], "s")
    assert await pay.process_incoming(late) == "late"
    await session.refresh(r3.payment)
    assert r3.payment.is_late
    await session.refresh(r3.order)
    assert r3.order.status == S.AWAITING_PAYMENT  # not auto-paid; money went to balance

    assert await pay.process_incoming(IncomingTx("e" * 64, 5, Dc(1), "hello", "s")) == "unmatched"
    assert await pay.process_incoming(IncomingTx("f" * 64, 6, Dc(1), None, "s")) == "unmatched"
    assert (await session.scalar(select(func.count()).select_from(UnmatchedTonTx))) == 2
    # a second transfer re-using an already confirmed comment is parked for review, not auto-credited
    again = IncomingTx("9" * 64, 7, r2.payment.amount, r2.instructions.extra["comment"], "s")
    assert await pay.process_incoming(again) == "unmatched"


async def test_stars_payment_idempotent_and_bot_stars_delivery(session):
    await seed(session)
    env = Env(session).with_bot_stars()
    u = await make_user(session, 77)
    res = await env.checkout.create_order(u, premium_req(await plan_id(session, 3), M.STARS))
    assert res.payment.amount == 1100 and res.payment.currency == "XTR"
    pay = env.checkout.payments
    ok, _ = await pay.validate_pre_checkout(res.payment.public_id, 77, 1100, "XTR")
    assert ok
    assert (await pay.validate_pre_checkout(res.payment.public_id, 77, 999, "XTR"))[0] is False
    assert (await pay.validate_pre_checkout(res.payment.public_id, 78, 1100, "XTR"))[0] is False
    await pay.handle_successful_stars_payment(res.payment.public_id, 77, "chg1", 1100)
    await pay.handle_successful_stars_payment(res.payment.public_id, 77, "chg1", 1100)  # redelivery
    assert (await session.scalar(select(func.count()).select_from(StarsTransaction))) == 1
    await env.fulfillment(env.providers).process_next()
    await session.refresh(res.order)
    assert res.order.status == S.COMPLETED and res.order.provider == ProviderCode.BOT_STARS
    assert env.stars.gifts == [(77, 3, 1000)]
    assert res.order.cost_amount == 1000 and res.order.cost_currency == "XTR"


async def test_stars_failure_refunds_via_telegram_then_balance_fallback(session):
    await seed(session)
    env = Env(session, mode="invalid")
    u = await make_user(session, 77)
    res = await env.checkout.create_order(u, premium_req(await plan_id(session, 3), M.STARS))
    await env.checkout.payments.handle_successful_stars_payment(res.payment.public_id, 77, "chgX", 1100)
    await env.fulfillment().process_next()
    await session.refresh(res.order)
    assert res.order.status == S.REFUNDED and env.stars.refunds == [(77, "chgX")]
    assert any("⭐" in t for t in env.messenger.texts(77))

    env.stars.fail_refund = True
    res2 = await env.checkout.create_order(u, premium_req(await plan_id(session, 3), M.STARS))
    await env.checkout.payments.handle_successful_stars_payment(res2.payment.public_id, 77, "chgY", 1100)
    await env.fulfillment().process_next()
    await session.refresh(u)
    assert u.balance_usd == res2.order.price_usd  # fell back to balance


async def test_temporary_failure_backoff_then_refund(session, env):
    env.mock.mode = "unavailable"
    u = await make_user(session, 2)
    await fund(session, u, 100)
    res = await env.checkout.create_order(u, premium_req(await plan_id(session, 3), M.BALANCE))
    price = res.order.price_usd
    f = env.fulfillment()
    for attempt in (1, 2):
        assert await f.process_next() is True
        await session.refresh(res.order)
        assert res.order.status == S.PAID and res.order.attempts == attempt and res.order.next_attempt_at > now_utc()
        res.order.next_attempt_at = now_utc() - timedelta(seconds=1)  # time passes
        await session.flush()
    assert await f.process_next() is True
    await session.refresh(res.order)
    assert res.order.status == S.REFUNDED and res.order.attempts == 3
    await session.refresh(u)
    assert u.balance_usd == Dc(100)  # paid price returned
    assert price > 0


async def test_uncertain_never_auto_refunded_and_admin_actions(session, env):
    env.mock.mode = "uncertain"
    u = await make_user(session, 2)
    await fund(session, u, 100)
    res = await env.checkout.create_order(u, premium_req(await plan_id(session, 3), M.BALANCE))
    f = env.fulfillment()
    await f.process_next()
    await session.refresh(res.order)
    assert res.order.status == S.NEEDS_REVIEW
    assert await f.process_next() is False  # not retried automatically
    await session.refresh(u)
    assert u.balance_usd < 100  # not refunded
    # admin retries, provider now works
    env.mock.mode = "ok"
    await f.retry(res.order, "admin:1")
    await f.process_next()
    await session.refresh(res.order)
    assert res.order.status == S.COMPLETED
    with pytest.raises(InvalidState):
        await f.refund(res.order, "admin:1")  # completed orders cannot be refunded


async def test_manual_complete_and_stuck_recovery(session, env):
    u = await make_user(session, 2)
    await fund(session, u, 100)
    res = await env.checkout.create_order(u, premium_req(await plan_id(session, 3), M.BALANCE))
    f = env.fulfillment()
    order = await f.claim_next()
    order.locked_at = now_utc() - timedelta(minutes=30)
    await session.flush()
    assert await f.recover_stuck() == 1
    await session.refresh(res.order)
    assert res.order.status == S.NEEDS_REVIEW
    await f.mark_completed_manually(res.order, "admin:1", "manual-ref")
    await session.refresh(res.order)
    assert res.order.status == S.COMPLETED and res.order.provider == ProviderCode.MANUAL


async def test_stars_product_rules_and_topup(session, env):
    u = await make_user(session, 2, username="alisher")
    with pytest.raises(MethodDisabled):
        await env.checkout.create_order(u, CreateOrderRequest(ProductType.STARS, M.STARS, stars_amount=500))
    res = await env.checkout.create_order(u, CreateOrderRequest(ProductType.STARS, M.TON, stars_amount=500))
    assert res.order.recipient_username == "alisher" and res.order.price_usd == Dc("8.03")
    noname = await make_user(session, 3, username=None)
    with pytest.raises(ValidationFailed):
        await env.checkout.create_order(noname, CreateOrderRequest(ProductType.STARS, M.TON, stars_amount=500))
    with pytest.raises(ValidationFailed):
        await env.checkout.create_order(u, CreateOrderRequest(ProductType.STARS, M.TON, stars_amount=10))
    # topup via TON
    top = await env.checkout.create_topup(u, Dc(10), M.TON)
    assert top.payment.public_id.startswith("TP-") and top.order is None
    tx = IncomingTx("1" * 64, 9, top.payment.amount, top.instructions.extra["comment"], "s")
    assert await env.checkout.payments.process_incoming(tx) == "confirmed"
    await session.refresh(u)
    assert u.balance_usd == Dc(10)
    with pytest.raises(ValidationFailed):
        await env.checkout.create_topup(u, Dc("0.1"), M.TON)


async def test_idempotency_key_and_expiry_and_cancel(session, env):
    u = await make_user(session, 2)
    pid = await plan_id(session, 3)
    r1 = await env.checkout.create_order(u, premium_req(pid, M.TON, idempotency_key="k1"))
    r2 = await env.checkout.create_order(u, premium_req(pid, M.TON, idempotency_key="k1"))
    assert r1.order.id == r2.order.id
    r1.payment.expires_at = now_utc() - timedelta(minutes=1)
    await session.flush()
    assert await env.checkout.payments.expire_stale() == 1
    await session.refresh(r1.order)
    assert r1.order.status == S.EXPIRED
    r3 = await env.checkout.create_order(u, premium_req(pid, M.TON))
    await env.checkout.cancel(r3.order, 2)
    await session.refresh(r3.order)
    assert r3.order.status == S.CANCELLED
    with pytest.raises(InvalidState):
        await env.checkout.orders.mark_paid(r3.order)


async def test_parallel_workers_deliver_once(session, env):
    import asyncio

    from app.core.db import session_maker
    from tests.helpers import Env as E

    u = await make_user(session, 2)
    await fund(session, u, 500)
    for _ in range(4):
        await env.checkout.create_order(u, premium_req(await plan_id(session, 3), M.BALANCE))
    await session.commit()
    mock = env.mock

    async def worker():
        async with session_maker()() as s:
            e = E(s)
            e.mock = mock
            e.providers = {ProviderCode.MOCK: mock}
            n = 0
            while await e.fulfillment().process_next():
                n += 1
            await s.commit()
            return n

    counts = await asyncio.gather(*[worker() for _ in range(4)])
    assert sum(counts) == 4 and len(mock.delivered) == 4 and len(set(mock.delivered)) == 4


async def test_ledger_reconciles(session, env):
    u = await make_user(session, 2)
    await fund(session, u, 100)
    for m in (3, 6):
        await env.checkout.create_order(u, premium_req(await plan_id(session, m), M.BALANCE))
    total = await session.scalar(select(func.sum(BalanceTransaction.amount_usd)).where(BalanceTransaction.user_id == 2))
    await session.refresh(u)
    assert total == u.balance_usd
