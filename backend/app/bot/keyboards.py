from typing import Literal

from aiogram.filters.callback_data import CallbackData
from aiogram.types import CopyTextButton, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

Style = Literal["primary", "success", "danger"]
Button = InlineKeyboardButton


def btn(
    text: str,
    cb: CallbackData | str | None = None,
    *,
    url: str | None = None,
    web_app: str | None = None,
    copy: str | None = None,
    pay: bool = False,
    style: Style | None = None,
) -> InlineKeyboardButton:
    """Inline button. ``style``: success=green (money/confirm), primary=blue (open/recommended), danger=red (cancel/risky)."""
    return InlineKeyboardButton(
        text=text,
        callback_data=cb.pack() if isinstance(cb, CallbackData) else cb,
        url=url,
        web_app=WebAppInfo(url=web_app) if web_app else None,
        copy_text=CopyTextButton(text=copy) if copy else None,
        pay=True if pay else None,
        style=style,
    )


def kb(*rows: list[InlineKeyboardButton] | InlineKeyboardButton | None) -> InlineKeyboardMarkup:
    out: list[list[InlineKeyboardButton]] = []
    for row in rows:
        if row is None:
            continue
        out.append([row] if isinstance(row, InlineKeyboardButton) else [b for b in row if b is not None])
    return InlineKeyboardMarkup(inline_keyboard=[r for r in out if r])
