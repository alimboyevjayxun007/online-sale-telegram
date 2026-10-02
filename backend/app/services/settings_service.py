import time
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import decrypt, encrypt
from app.models import Setting

DEFAULTS: dict[str, Any] = {
    "payments.ton.enabled": True,
    "payments.stars.enabled": True,
    "payments.balance.enabled": True,
    "payments.topup.stars.enabled": True,
    "payments.invoice_ttl_minutes": 20,
    "pricing.network_fee_ton": "0.05",
    "pricing.min_margin_percent": "2",
    "pricing.round_step_usd": "0.05",
    "pricing.stars.markup_percent": "7",
    "pricing.stars.max_amount": 100000,
    "pricing.star_usd_rate": "0.013",
    "pricing.topup.min_usd": "1",
    "pricing.topup.max_usd": "5000",
    "pricing.premium_default_markup_percent": "8",
    "fulfillment.premium.priority": ["fragment_direct", "fragment_api", "bot_stars"],
    "fulfillment.stars_paid_strategy": "bot_stars",
    "fulfillment.max_attempts": 3,
    "fulfillment.auto_refund": True,
    "fragment.mode": "direct",
    "fragment.cookies": "",
    "hot_wallet.address": "",
    "hot_wallet.reserve_ton": "30",
    "hot_wallet.low_balance_alert_ton": "15",
    "hot_wallet.sweep_enabled": False,
    "hot_wallet.sweep_threshold_ton": "100",
    "hot_wallet.daily_withdraw_limit_ton": "1000",
    "hot_wallet.frozen": False,
    "referral.enabled": True,
    "referral.percent": "2",
    "bot.maintenance": False,
    "bot.support_username": "",
    "bot.mandatory_subscription": True,
    "notify.log_chat_id": None,
    "notify.events": {
        "order_paid": True,
        "order_completed": True,
        "order_failed": True,
        "new_user": False,
    },
    "provider.star_unit_cost_ton": "",  # filled by a live provider price feed when available
    "pricing.fallback_cost_usd": {"3": "11.99", "6": "15.99", "12": "28.99"},  # Fragment USD list prices
    "pricing.fallback_star_cost_usd": "0.015",
    "ton_watcher.last_lt": 0,
    "admin.balance_limit_usd": "50",
}
SECRET_KEYS = {"fragment.cookies"}
_TTL = 5.0
_cache: dict[str, tuple[float, Any]] = {}


def clear_cache() -> None:
    _cache.clear()


class SettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, key: str) -> Any:
        hit = _cache.get(key)
        if hit and time.monotonic() - hit[0] < _TTL:
            return hit[1]
        row = await self.session.get(Setting, key)
        value = row.value if row is not None else DEFAULTS.get(key)
        if row is not None and row.is_secret and value:
            value = decrypt(value, get_settings().encryption_key.get_secret_value())
        if key == "notify.log_chat_id" and value is None:
            value = get_settings().log_chat_id
        _cache[key] = (time.monotonic(), value)
        return value

    async def set(self, key: str, value: Any, actor: int | None = None) -> None:
        if key not in DEFAULTS:
            raise KeyError(key)
        secret = key in SECRET_KEYS
        stored = encrypt(value, get_settings().encryption_key.get_secret_value()) if secret and value else value
        stmt = insert(Setting).values(key=key, value=stored, is_secret=secret, updated_by=actor)
        stmt = stmt.on_conflict_do_update(
            index_elements=["key"],
            set_={"value": stored, "is_secret": secret, "updated_by": actor, "updated_at": func.now()},
        )
        await self.session.execute(stmt)
        _cache.pop(key, None)

    async def get_all(self, mask_secrets: bool = True) -> dict[str, Any]:
        rows = {r.key: r for r in (await self.session.scalars(select(Setting))).all()}
        out: dict[str, Any] = {}
        for key, default in DEFAULTS.items():
            if key in SECRET_KEYS:
                out[key] = "***" if (key in rows and rows[key].value) else ""
            else:
                out[key] = rows[key].value if key in rows else default
        return out
