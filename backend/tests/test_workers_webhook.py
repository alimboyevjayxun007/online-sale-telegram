import asyncio
from decimal import Decimal as Dc

import httpx
import pytest
import respx
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api.runtime import Runtime, Services, set_runtime
from app.core.db import session_maker
from app.core.enums import OrderStatus as S
from app.core.enums import PaymentMethod as M
from app.core.enums import ProductType, ProviderCode
from app.core.errors import ProviderUncertain, RecipientInvalid
from app.main import create_app
from app.models import Order
from app.providers.fulfillment.fragment import FragmentDirectProvider, FragmentWebClient
from app.providers.fulfillment.mock import MockProvider
from app.providers.ton.chain import IncomingTx
from app.services.checkout_service import CreateOrderRequest
from app.services.settings_service import SettingsService
from app.workers import jobs
from app.workers.runner import SCHEDULES, supervise
from tests.factories import make_user
from tests.helpers import FakeMessenger, FakeStars, fund, plan_id, seed


class ScriptedChain:
    def __init__(self):
        self.txs: list[IncomingTx] = []
        self.asked_after: list[int] = []

    async def get_incoming(self, address, after_lt=0):
        self.asked_after.append(after_lt)
        return [t for t in self.txs if t.lt > after_lt]

    async def get_balance(self, address):
        return Dc(5)


@pytest.fixture
async def rt(session):
    await seed(session)
    await SettingsService(session).set("hot_wallet.address", "UQHot")
    await session.commit()
    r = Runtime(messenger=FakeMessenger(), stars=FakeStars(), mock=MockProvider(), chain=ScriptedChain())
    set_runtime(r)
    yield r
    set_runtime(Runtime())


async def test_ton_watcher_job_confirms_then_fulfillment_job_delivers(session, rt):
    u = await make_user(session, 7)
    svc = Services(session, rt)
    res = await svc.checkout.create_order(
        u, CreateOrderRequest(ProductType.PREMIUM, M.TON, plan_id=await plan_id(session, 3))
    )
    await session.commit()
    rt.chain.txs.append(IncomingTx("a" * 64, 100, res.payment.amount, res.payment.ton_comment, "UQs"))
    await jobs.ton_watcher(rt)
    await jobs.ton_watcher(rt)  # second tick: cursor moved, nothing re-processed
    assert rt.chain.asked_after == [0, 100]
    await jobs.fulfillment(rt)
    async with session_maker()() as s:
        order = await s.scalar(select(Order))
        assert order.status == S.COMPLETED
    assert any("Tayyor" in t for t in rt.messenger.texts(7))
    # low balance alert goes to the owner/log chat once per hour
    await jobs.hot_wallet(rt)
    await jobs.hot_wallet(rt)
    low = [t for _, t in rt.messenger.sent if "Hot wallet balansi past" in t]
    assert len(low) == 1


async def test_stats_job_expirer_reconciliation_heartbeat_reports(session, rt):
    u = await make_user(session, 8)
    await fund(session, u, 100)
    svc = Services(session, rt)
    await svc.checkout.create_order(
        u, CreateOrderRequest(ProductType.PREMIUM, M.BALANCE, plan_id=await plan_id(session, 3))
    )
    await session.commit()
    await jobs.fulfillment(rt)
    await jobs.stats(rt)
    await jobs.expirer(rt)
    await jobs.reconciliation(rt)
    await jobs.heartbeat(rt)
    await jobs.reports(rt)
    from app.core.redis import get_redis

    assert await get_redis().get("worker:heartbeat")
    assert not [t for _, t in rt.messenger.sent if "mos emas" in t]  # ledger reconciles
    async with session_maker()() as s:
        from app.models import DailyStats

        rows = (await s.scalars(select(DailyStats))).all()
        assert len(rows) == 2 and max(r.orders_completed for r in rows) == 1


async def test_supervisor_survives_failing_job_and_alerts(session, rt):
    calls = {"n": 0}

    async def bad(_):
        calls["n"] += 1
        raise RuntimeError("boom")

    from app.workers.runner import Schedule

    stop = asyncio.Event()
    task = asyncio.create_task(supervise(Schedule("bad", bad, 0.001), rt, stop))
    for _ in range(300):
        await asyncio.sleep(0.02)
        if calls["n"] >= 3:
            break
    stop.set()
    await asyncio.wait_for(task, 5)
    assert calls["n"] >= 3
    assert any("3 marta yiqildi" in t for _, t in rt.messenger.sent)
    assert {s.name for s in SCHEDULES} >= {"ton_watcher", "fulfillment", "broadcast", "heartbeat"}


async def test_telegram_webhook_secret_and_dispatch(session, rt, monkeypatch):
    from app.bot.setup import create_dispatcher
    from app.core.config import get_settings
    from tests.fake_telegram import make_bot

    monkeypatch.setenv("WEBHOOK_SECRET", "s3cret")
    get_settings.cache_clear()
    bot, tg = make_bot()
    app = create_app()
    app.state.bot, app.state.dp = bot, create_dispatcher(Runtime(bot=bot, messenger=rt.messenger, stars=rt.stars))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        upd = {"update_id": 1, "message": {"message_id": 1, "date": 1700000000, "chat": {"id": 55, "type": "private"},
               "from": {"id": 55, "is_bot": False, "first_name": "W", "language_code": "uz"}, "text": "/start"}}  # fmt: skip
        assert (await c.post("/tg/webhook", json=upd)).status_code == 401
        assert (
            await c.post("/tg/webhook", json=upd, headers={"X-Telegram-Bot-Api-Secret-Token": "bad"})
        ).status_code == 401
        r = await c.post("/tg/webhook", json=upd, headers={"X-Telegram-Bot-Api-Secret-Token": "s3cret"})
        assert r.status_code == 200
    assert "Tilni tanlang" in tg.last_text()
    get_settings.cache_clear()


# ---------------- Fragment adapter against a mocked website ----------------
class RecordingSigner:
    address = "UQHot"

    def __init__(self, fail=False):
        self.sent, self.fail = [], fail

    async def send(self, to, amount_nano, comment=None, body_b64=None):
        if self.fail:
            raise RuntimeError("network")
        self.sent.append((to, amount_nano, body_b64))
        return "cd" * 32


def fragment_mock(router, *, found=True, init_ok=True, tx=True):
    router.get("https://fragment.com/premium/gift").mock(
        return_value=httpx.Response(200, text='<script>"apiUrl":"\\/api?hash=abc123def"</script>')
    )

    def handler(request):
        form = dict(x.split("=", 1) for x in request.content.decode().split("&"))
        m = form["method"]
        if m == "searchPremiumGiftRecipient":
            return httpx.Response(
                200,
                json={"ok": True, "found": {"recipient": "RCP1", "name": "Ali"}}
                if found
                else {"ok": False, "error": "No Telegram users found."},
            )
        if m == "initGiftPremiumRequest":
            return httpx.Response(200, json={"req_id": "REQ9"} if init_ok else {"error": "nope"})
        if m == "getGiftPremiumLink":
            return httpx.Response(
                200,
                json={
                    "ok": True,
                    "transaction": {
                        "messages": [{"address": "EQFragment", "amount": "4000000000", "payload": "te6cc"}]
                    },
                }
                if tx
                else {"error": "x"},
            )
        return httpx.Response(404)

    router.post(url__regex=r"https://fragment.com/api\?hash=abc123def").mock(side_effect=handler)


def frag_order():
    return Order(
        public_id="PR-X",
        user_id=1,
        product_type=ProductType.PREMIUM,
        plan_months=3,
        recipient_username="durov_x",
        payment_method=M.TON,
    )


@respx.mock
async def test_fragment_direct_happy_path_and_resolve():
    fragment_mock(respx)
    signer = RecordingSigner()
    p = FragmentDirectProvider(FragmentWebClient({"stel_ssid": "x"}, {"address": "UQHot", "chain": "-239"}), signer)
    info = await p.resolve_recipient("durov_x", "premium", 3)
    assert info.found and info.name == "Ali"
    res = await p.deliver(frag_order())
    assert res.cost_amount == Dc(4) and res.cost_currency == "TON" and res.provider_ref == "cd" * 32
    assert signer.sent == [("EQFragment", 4_000_000_000, "te6cc")]


@respx.mock
async def test_fragment_failure_classification():
    fragment_mock(respx, found=False)
    p = FragmentDirectProvider(FragmentWebClient({}, {}), RecordingSigner())
    with pytest.raises(RecipientInvalid):
        await p.deliver(frag_order())
    respx.reset()
    fragment_mock(respx)
    p = FragmentDirectProvider(FragmentWebClient({}, {}), RecordingSigner(fail=True))
    with pytest.raises(ProviderUncertain):  # money may have left: never auto-retry
        await p.deliver(frag_order())
    assert await FragmentDirectProvider(None, None).is_available() is False
    _ = ProviderCode
