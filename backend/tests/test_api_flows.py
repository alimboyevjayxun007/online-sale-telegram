from decimal import Decimal as Dc

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.runtime import Runtime, set_runtime
from app.core.enums import ProviderCode
from app.core.security import build_init_data
from app.main import create_app
from app.models import User
from app.providers.fulfillment.mock import MockProvider
from tests.helpers import FakeMessenger, FakeStars, seed

TOKEN = "123456:TESTTOKENTESTTOKENTESTTOKENTESTTOKEN"


def auth(uid):
    return {
        "Authorization": "tma "
        + build_init_data({"id": uid, "first_name": f"U{uid}", "username": f"user{uid}x"}, TOKEN)
    }


@pytest.fixture
async def api(session):
    await seed(session)
    await session.commit()
    rt = Runtime(messenger=FakeMessenger(), stars=FakeStars(), mock=MockProvider())
    set_runtime(rt)
    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://t") as c:
        c.rt = rt
        yield c
    set_runtime(Runtime())


async def test_catalog_and_quotes(api):
    r = await api.get("/api/v1/catalog", headers=auth(10))
    body = r.json()
    plans = {p["months"]: p for p in body["plans"]}
    assert plans[3]["price_usd"] == "13.150000" and plans[1]["coming_soon"] is True
    assert body["methods"]["ton"] is True and body["star_packages"][0]["amount"] == 50
    q = await api.post("/api/v1/catalog/stars-quote", headers=auth(10), json={"amount": 500})
    assert q.json()["price_usd"] == "8.030000"
    assert (await api.post("/api/v1/catalog/stars-quote", headers=auth(10), json={"amount": 5})).status_code == 400


async def test_full_mini_app_order_via_balance(api, session):
    h = auth(11)
    await api.get("/api/v1/me", headers=h)
    session.expire_all()
    from tests.helpers import fund

    u = await session.get(User, 11)
    await fund(session, u, 40)
    await session.commit()
    cat = (await api.get("/api/v1/catalog", headers=h)).json()
    plan_id = [p for p in cat["plans"] if p["months"] == 12][0]["id"]
    body = {"product_type": "premium", "plan_id": plan_id, "payment_method": "balance", "recipient": {"type": "self"}}
    r = await api.post("/api/v1/orders", headers={**h, "Idempotency-Key": "abc"}, json=body)
    assert r.status_code == 200, r.text
    order = r.json()["order"]
    assert order["status"] == "paid" and order["price_usd"] == "31.500000"
    again = await api.post("/api/v1/orders", headers={**h, "Idempotency-Key": "abc"}, json=body)
    assert again.json()["order"]["public_id"] == order["public_id"]
    # worker delivers
    from app.api.runtime import Services
    from app.core.db import session_maker

    async with session_maker()() as s:
        svc = Services(s, api.rt)
        assert await (await svc.fulfillment()).process_next()
        await s.commit()
    got = (await api.get(f"/api/v1/orders/{order['public_id']}", headers=h)).json()
    assert got["status"] == "completed" and [e["status"] for e in got["events"]][-1] == "completed"
    w = (await api.get("/api/v1/wallet", headers=h)).json()
    assert w["balance_usd"] == "8.500000"
    lst = (await api.get("/api/v1/orders", headers=h)).json()
    assert len(lst["items"]) == 1
    assert (await api.get(f"/api/v1/orders/{order['public_id']}", headers=auth(12))).status_code == 404  # not yours


async def test_ton_order_returns_instructions_and_stars_link(api, session):
    from app.services.settings_service import SettingsService

    await SettingsService(session).set("hot_wallet.address", "UQHot")
    await session.commit()
    h = auth(13)
    cat = (await api.get("/api/v1/catalog", headers=h)).json()
    pid = [p for p in cat["plans"] if p["months"] == 3][0]["id"]
    r = await api.post(
        "/api/v1/orders", headers=h, json={"product_type": "premium", "plan_id": pid, "payment_method": "ton"}
    )
    ins = r.json()["payment_instructions"]
    assert ins["address"] == "UQHot" and ins["comment"].startswith("PM-") and ins["amount_nano"] == "4390000000"
    r2 = await api.post(
        "/api/v1/orders", headers=h, json={"product_type": "premium", "plan_id": pid, "payment_method": "stars"}
    )
    pay_id = r2.json()["payment_instructions"]["payment_id"]
    link = await api.post(f"/api/v1/payments/{pay_id}/stars-link", headers=h)
    assert link.json()["invoice_link"].startswith("https://t.me/$inv_PM-")
    bad = await api.post(
        "/api/v1/orders", headers=h, json={"product_type": "stars", "stars_amount": 100, "payment_method": "stars"}
    )
    assert bad.json()["error"]["code"] == "METHOD_DISABLED"
    # topup + referral
    t = await api.post("/api/v1/wallet/topup", headers=h, json={"amount_usd": "10", "method": "ton"})
    assert t.json()["payment_instructions"]["comment"].startswith("TP-")
    assert (await api.get("/api/v1/referral", headers=h)).json()["link"] == "https://t.me/TestBot?start=ref_13"


async def test_recipient_resolve_with_mock_and_validation(api):
    h = auth(14)
    r = await api.post("/api/v1/recipients/resolve", headers=h, json={"username": "@durov_x"})
    assert r.json()["found"] is True and r.json()["username"] == "durov_x"
    nf = await api.post("/api/v1/recipients/resolve", headers=h, json={"username": "nouser_1"})
    assert nf.json()["found"] is False
    assert (await api.post("/api/v1/recipients/resolve", headers=h, json={"username": "a b"})).status_code == 400


async def test_admin_endpoints_rbac_and_actions(api, session):
    owner, plain = auth(1000), auth(20)
    await api.get("/api/v1/me", headers=owner)
    await api.get("/api/v1/me", headers=plain)
    for path in ("/dashboard", "/orders", "/users", "/finance/overview", "/settings", "/audit-logs"):
        assert (await api.get("/api/v1/admin" + path, headers=plain)).status_code == 403
    d = await api.get("/api/v1/admin/dashboard?period=today", headers=owner)
    assert d.status_code == 200 and d.json()["current"]["orders_completed"] == 0
    assert (await api.get("/api/v1/admin/dashboard?period=bogus", headers=owner)).status_code == 400
    r = await api.post("/api/v1/admin/admins", headers=owner, json={"user_id": 20, "role": "support"})
    assert r.status_code == 200
    assert (await api.get("/api/v1/admin/orders", headers=plain)).status_code == 200  # support can view
    assert (await api.get("/api/v1/admin/dashboard", headers=plain)).status_code == 403  # but not stats
    assert (
        await api.post("/api/v1/admin/finance/withdraw", headers=plain, json={"amount_ton": "1"})
    ).status_code == 403
    assert (
        await api.post("/api/v1/admin/admins", headers=plain, json={"user_id": 20, "role": "admin"})
    ).status_code == 403
    s = await api.put("/api/v1/admin/settings", headers=owner, json={"values": {"referral.percent": "3"}})
    assert s.status_code == 200
    assert (await api.get("/api/v1/admin/settings", headers=owner)).json()["referral.percent"] == "3"
    assert (
        await api.put("/api/v1/admin/settings", headers=owner, json={"values": {"ton_watcher.last_lt": 5}})
    ).status_code == 400
    ts = await api.get("/api/v1/admin/stats/timeseries?period=custom&frm=2026-10-01&to=2026-10-03", headers=owner)
    assert ts.status_code == 200
    assert (
        (await api.get("/api/v1/admin/stats/export.xlsx?period=today", headers=owner))
        .headers["content-type"]
        .startswith("application/vnd")
    )
    p = await api.post(
        "/api/v1/admin/promo-codes", headers=owner, json={"code": "KUZ5", "type": "percent", "value": "5"}
    )
    assert p.status_code == 200
    pv = await api.post(
        "/api/v1/promo/validate", headers=owner, json={"code": "kuz5", "product_type": "premium", "plan_id": 2}
    )
    assert pv.json()["valid"] is True
    audit = (await api.get("/api/v1/admin/audit-logs", headers=owner)).json()
    assert {"admin.set", "settings.update", "promo.create"} <= {a["action"] for a in audit}
    mm = await api.put("/api/v1/admin/settings", headers=owner, json={"values": {"bot.maintenance": True}})
    assert mm.status_code == 200
    blocked = await api.post(
        "/api/v1/orders", headers=auth(30), json={"product_type": "premium", "plan_id": 2, "payment_method": "ton"}
    )
    assert blocked.json()["error"]["code"] == "MAINTENANCE"
    _ = (Dc, ProviderCode)


async def test_payment_instructions_endpoint(api, session):
    from app.services.settings_service import SettingsService

    await SettingsService(session).set("hot_wallet.address", "UQHot")
    await session.commit()
    h = auth(15)
    cat = (await api.get("/api/v1/catalog", headers=h)).json()
    pid = [p for p in cat["plans"] if p["months"] == 3][0]["id"]
    o = (
        await api.post(
            "/api/v1/orders", headers=h, json={"product_type": "premium", "plan_id": pid, "payment_method": "ton"}
        )
    ).json()
    pay_id = o["payment_instructions"]["payment_id"]
    r = (await api.get(f"/api/v1/payments/{pay_id}/instructions", headers=h)).json()
    assert r["address"] == "UQHot" and r["comment"] == o["payment_instructions"]["comment"] and r["status"] == "pending"
    assert (await api.get(f"/api/v1/payments/{pay_id}/instructions", headers=auth(16))).status_code == 404


async def test_maintenance_blocks_everything_for_users_but_not_staff(api, session):
    from app.services.settings_service import SettingsService

    await SettingsService(session).set("bot.maintenance", True)
    await session.commit()
    r = await api.get("/api/v1/me", headers=auth(77))
    assert r.status_code == 503 and r.json()["error"]["code"] == "MAINTENANCE"
    assert (await api.get("/api/v1/catalog", headers=auth(77))).status_code == 503
    assert (await api.get("/api/v1/me", headers=auth(1000))).status_code == 200  # owner passes
    assert (await api.get("/api/v1/admin/dashboard", headers=auth(1000))).status_code == 200
