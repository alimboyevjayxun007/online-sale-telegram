import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import build_init_data
from app.main import create_app
from app.services.settings_service import SettingsService

TOKEN = "123456:TESTTOKENTESTTOKENTESTTOKENTESTTOKEN"


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://t") as c:
        yield c


def auth(uid=42, **extra):
    return {
        "Authorization": "tma "
        + build_init_data({"id": uid, "first_name": "Ali", "language_code": "ru", **extra}, TOKEN)
    }


async def test_me_creates_user_and_language(client):
    r = await client.get("/api/v1/me", headers=auth())
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == 42 and body["language"] == "ru" and body["is_admin"] is False
    assert body["ref_link"] == "https://t.me/TestBot?start=ref_42"
    r = await client.patch("/api/v1/me", headers=auth(), json={"language": "en"})
    assert r.json() == {"language": "en"}
    assert (await client.patch("/api/v1/me", headers=auth(), json={"language": "xx"})).status_code == 400


async def test_me_owner_role(client):
    r = await client.get("/api/v1/me", headers=auth(uid=1000))
    assert r.json()["role"] == "owner"


async def test_me_rejects_bad_auth(client):
    assert (await client.get("/api/v1/me")).status_code == 401
    r = await client.get("/api/v1/me", headers={"Authorization": "tma bad"})
    assert r.json()["error"]["code"] == "INIT_DATA_INVALID"


async def test_settings_defaults_override_and_secret(session):
    s = SettingsService(session)
    assert await s.get("referral.percent") == "2"
    await s.set("referral.percent", "3", actor=1)
    assert await s.get("referral.percent") == "3"
    await s.set("fragment.cookies", "stel_ssid=abc", actor=1)
    assert await s.get("fragment.cookies") == "stel_ssid=abc"
    assert (await s.get_all())["fragment.cookies"] == "***"
    with pytest.raises(KeyError):
        await s.set("nope", 1)
