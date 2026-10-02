from typing import Any, Protocol

import structlog

from app.core.config import get_settings
from app.i18n import t
from app.models import Order, User
from app.services.settings_service import SettingsService

log = structlog.get_logger()


class DeliveryBlocked(Exception):
    """The user blocked the bot / deactivated the account (HTTP 403)."""


class DeliveryRetry(Exception):
    def __init__(self, seconds: float) -> None:
        super().__init__(f"retry after {seconds}")
        self.seconds = seconds


class Messenger(Protocol):
    async def send_content(self, chat_id: int, content: dict[str, Any]) -> None: ...

    async def send(self, chat_id: int, text: str, reply_markup: Any = None) -> int | None: ...

    async def edit(self, chat_id: int, message_id: int, text: str, reply_markup: Any = None) -> bool: ...


class NullMessenger:
    async def send_content(self, chat_id: int, content: dict[str, Any]) -> None:
        return None

    async def send(self, chat_id: int, text: str, reply_markup: Any = None) -> int | None:
        return None

    async def edit(self, chat_id: int, message_id: int, text: str, reply_markup: Any = None) -> bool:
        return False


class NotificationService:
    def __init__(self, messenger: Messenger, settings: SettingsService) -> None:
        self.m, self.settings = messenger, settings

    async def notify_user(self, user: User, key: str, reply_markup: Any = None, **kw: Any) -> int | None:
        try:
            return await self.m.send(user.id, t(user.language, key, **kw), reply_markup)
        except Exception as exc:  # noqa: BLE001 - never break money flows because of a failed message
            log.warning("notify_user_failed", user_id=user.id, error=str(exc))
            return None

    async def notify_order(self, order: Order, user: User, key: str, reply_markup: Any = None, **kw: Any) -> None:
        text = t(user.language, key, **kw)
        try:
            if order.bot_message_id and await self.m.edit(user.id, order.bot_message_id, text, reply_markup):
                return
            msg_id = await self.m.send(user.id, text, reply_markup)
            if msg_id and not order.bot_message_id:
                order.bot_message_id = msg_id
        except Exception as exc:  # noqa: BLE001
            log.warning("notify_order_failed", order=order.public_id, error=str(exc))

    async def log_chat_id(self) -> int | None:
        chat = await self.settings.get("notify.log_chat_id")
        return int(chat) if chat else (get_settings().owner_telegram_id or None)

    async def alert(self, text: str, level: str = "info", reply_markup: Any = None, event: str | None = None) -> None:
        if event is not None:
            events = await self.settings.get("notify.events") or {}
            if not events.get(event, True):
                return
        chat = await self.log_chat_id()
        if not chat:
            return
        icon = {"info": "ℹ️", "warn": "⚠️", "crit": "🔴"}.get(level, "ℹ️")
        try:
            await self.m.send(chat, f"{icon} {text}", reply_markup)
        except Exception as exc:  # noqa: BLE001
            log.warning("alert_failed", error=str(exc))
