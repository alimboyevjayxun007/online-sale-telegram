from typing import Any

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import InlineKeyboardMarkup, LabeledPrice

from app.services.notification_service import DeliveryBlocked, DeliveryRetry


class AiogramMessenger:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def send(self, chat_id: int, text: str, reply_markup: Any = None) -> int | None:
        msg = await self.bot.send_message(chat_id, text, reply_markup=reply_markup)
        return msg.message_id

    async def edit(self, chat_id: int, message_id: int, text: str, reply_markup: Any = None) -> bool:
        try:
            await self.bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)
            return True
        except Exception:  # noqa: BLE001 - message too old / not modified → caller sends a fresh one
            return False

    async def send_content(self, chat_id: int, content: dict[str, Any]) -> None:
        markup = None
        if content.get("buttons"):
            from app.bot.keyboards import btn, kb

            markup = kb(*[[btn(b["text"], url=b["url"]) for b in row] for row in content["buttons"]])
        try:
            kind, text = content.get("type", "text"), content.get("text") or ""
            if kind == "photo":
                await self.bot.send_photo(chat_id, content["media_file_id"], caption=text or None, reply_markup=markup)
            elif kind == "video":
                await self.bot.send_video(chat_id, content["media_file_id"], caption=text or None, reply_markup=markup)
            elif kind == "animation":
                await self.bot.send_animation(
                    chat_id, content["media_file_id"], caption=text or None, reply_markup=markup
                )
            else:
                await self.bot.send_message(chat_id, text, reply_markup=markup)
        except TelegramForbiddenError as exc:
            raise DeliveryBlocked() from exc
        except TelegramRetryAfter as exc:
            raise DeliveryRetry(float(exc.retry_after)) from exc


class AiogramStarsGateway:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def gift_premium(self, user_id: int, months: int, star_count: int) -> None:
        await self.bot.gift_premium_subscription(user_id=user_id, month_count=months, star_count=star_count)

    async def star_balance(self) -> int:
        return int((await self.bot.get_my_star_balance()).amount)

    async def refund_star_payment(self, user_id: int, charge_id: str) -> None:
        await self.bot.refund_star_payment(user_id=user_id, telegram_payment_charge_id=charge_id)

    async def create_invoice_link(self, title: str, description: str, payload: str, amount: int) -> str:
        return await self.bot.create_invoice_link(
            title=title,
            description=description,
            payload=payload,
            currency="XTR",
            prices=[LabeledPrice(label=title[:32], amount=amount)],
        )

    async def send_invoice(self, chat_id: int, title: str, description: str, payload: str, amount: int) -> int:
        from app.bot.callbacks import Pay
        from app.bot.keyboards import btn, kb

        markup: InlineKeyboardMarkup = kb(
            btn(f"⭐ {amount}", pay=True, style="success"), btn("✖️", Pay(a="cancel_stars", id=payload), style="danger")
        )
        msg = await self.bot.send_invoice(
            chat_id=chat_id, title=title, description=description, payload=payload, currency="XTR",
            prices=[LabeledPrice(label=title[:32], amount=amount)], reply_markup=markup,
        )  # fmt: skip
        return msg.message_id
