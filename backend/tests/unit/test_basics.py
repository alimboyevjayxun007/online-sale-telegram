from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.logging import _mask
from app.main import create_app


def test_health() -> None:
    assert TestClient(create_app()).get("/api/health").json() == {"status": "ok"}


def test_production_validation_lists_missing() -> None:
    missing = Settings(app_env="production", _env_file=None).validate_for_production()
    assert "BOT_TOKEN" in missing and "ADMIN_TON_ADDRESS" in missing


def test_log_masking() -> None:
    fake = "1234567890:" + "A" * 35
    out = _mask(None, "", {"bot_token": "x", "msg": f"t {fake}"})
    assert out["bot_token"] == "***" and fake not in out["msg"]
