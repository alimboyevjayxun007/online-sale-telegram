from datetime import datetime
from decimal import Decimal
from typing import Any

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from app.core.config import get_settings
from app.core.timeutil import tz
from app.i18n import t
from app.models import Order, User


def usd(v: Decimal | str | float) -> str:
    return f"{Decimal(str(v)):.2f} $"


def uzs(v: int | Decimal) -> str:
    return f"{int(v):,}".replace(",", " ") + " so'm"


def ton(v: Decimal | str) -> str:
    return f"{Decimal(str(v)):.2f}"


def stars_fmt(v: int) -> str:
    return f"{int(v):,}".replace(",", " ") + " ⭐"


def dt(v: datetime) -> str:
    return v.astimezone(tz()).strftime("%d.%m.%Y %H:%M")


async def show(ev: Message | CallbackQuery, text: str, markup: Any = None, *, new: bool = False) -> Message:
    """One-message-per-screen: edit in place for callbacks (BotFather style), send for messages."""
    if isinstance(ev, CallbackQuery):
        msg = ev.message
        assert isinstance(msg, Message)
        if not new:
            try:
                await msg.edit_text(text, reply_markup=markup)
                return msg
            except TelegramBadRequest as exc:
                if "not modified" in str(exc):
                    return msg
        return await msg.answer(text, reply_markup=markup)
    return await ev.answer(text, reply_markup=markup)


async def toast(cb: CallbackQuery, text: str = "", alert: bool = False) -> None:
    await cb.answer(text, show_alert=alert)


def webapp_url(path: str = "") -> str:
    return get_settings().webapp_url.rstrip("/") + path


def who_label(lang: str, order_or_flow: dict[str, Any] | Order, user: User) -> str:
    if isinstance(order_or_flow, Order):
        o = order_or_flow
        if o.recipient_type.value == "self":
            return t(lang, "who_self")
        return f"@{o.recipient_username}" if o.recipient_username else str(o.recipient_user_id)
    f = order_or_flow
    if f.get("rtype") == "self":
        return f"@{user.username}" if user.username else t(lang, "who_self")
    return f"@{f['ruser']}" if f.get("ruser") else str(f.get("rid"))


def order_what(lang: str, o: Order) -> str:
    if o.plan_months:
        return t(lang, "what_prem", months=o.plan_months)
    return t(lang, "what_star", amount=stars_fmt(o.stars_amount or 0))
