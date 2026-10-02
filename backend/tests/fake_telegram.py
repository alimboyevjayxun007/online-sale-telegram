"""A fake Telegram: records every Bot API call and lets tests feed updates into the real dispatcher."""

from datetime import datetime
from typing import Any

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.base import BaseSession
from aiogram.enums import ParseMode
from aiogram.methods import TelegramMethod
from aiogram.types import CallbackQuery, Chat, Message, PreCheckoutQuery, SuccessfulPayment, Update
from aiogram.types import User as TgUser

BOT_ID = 123456


class FakeSession(BaseSession):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[TelegramMethod[Any]] = []
        self.next_id = 5000
        self.balance = 10_000

    async def close(self) -> None:
        return None

    async def stream_content(self, *a: Any, **k: Any):  # type: ignore[no-untyped-def]
        yield b""

    async def make_request(self, bot: Bot, method: TelegramMethod[Any], timeout: int | None = None) -> Any:  # noqa: ASYNC109
        self.calls.append(method)
        name = type(method).__name__
        if name in ("SendMessage", "EditMessageText", "SendInvoice", "SendDocument", "SendPhoto"):
            self.next_id += 1
            chat_id = getattr(method, "chat_id", 0)
            msg = Message(message_id=getattr(method, "message_id", None) or self.next_id, date=datetime.now(),
                           chat=Chat(id=int(chat_id) if isinstance(chat_id, int) else 0, type="private"),
                           text=getattr(method, "text", None), from_user=TgUser(id=BOT_ID, is_bot=True, first_name="bot"))  # fmt: skip
            return msg.as_(bot)
        if name == "GetMyStarBalance":
            from aiogram.types import StarAmount

            return StarAmount(amount=self.balance)
        if name == "GetChatMember":
            from aiogram.types import ChatMemberMember

            return ChatMemberMember(user=TgUser(id=1, is_bot=False, first_name="x"))
        return True

    # ----- helpers for tests -----
    def of(self, kind: str) -> list[Any]:
        return [c for c in self.calls if type(c).__name__ == kind]

    def last_text(self) -> str:
        msgs = [c for c in self.calls if type(c).__name__ in ("SendMessage", "EditMessageText")]
        return msgs[-1].text if msgs else ""  # type: ignore[attr-defined]

    def last_markup(self) -> Any:
        msgs = [c for c in self.calls if type(c).__name__ in ("SendMessage", "EditMessageText") and c.reply_markup]  # type: ignore[attr-defined]
        return msgs[-1].reply_markup if msgs else None  # type: ignore[attr-defined]

    def buttons(self) -> list[Any]:
        m = self.last_markup()
        return [b for row in m.inline_keyboard for b in row] if m and hasattr(m, "inline_keyboard") else []

    def texts(self) -> list[str]:
        return [c.text for c in self.calls if type(c).__name__ in ("SendMessage", "EditMessageText")]  # type: ignore[attr-defined]


def make_bot(token: str = "123456:TESTTOKENTESTTOKENTESTTOKENTESTTOKEN") -> tuple[Bot, FakeSession]:
    session = FakeSession()
    bot = Bot(token, session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    return bot, session


class Client:
    """Simulates one Telegram user talking to the bot."""

    def __init__(
        self, dp: Any, bot: Bot, uid: int, username: str | None = None, lang: str = "uz", name: str = "Ali"
    ) -> None:
        self.dp, self.bot, self.uid = dp, bot, uid
        self.tg = TgUser(id=uid, is_bot=False, first_name=name, username=username, language_code=lang)
        self.update_id = uid * 1000
        self.msg_id = 1

    def _msg(self, **kw: Any) -> Message:
        self.msg_id += 1
        return Message(
            message_id=self.msg_id, date=datetime.now(), chat=Chat(id=self.uid, type="private"), from_user=self.tg, **kw
        )

    async def _feed(self, **upd: Any) -> None:
        self.update_id += 1
        await self.dp.feed_update(self.bot, Update(update_id=self.update_id, **upd))

    async def say(self, text: str) -> None:
        await self._feed(message=self._msg(text=text))

    async def press(self, data: str, message_id: int = 777) -> None:
        cb = CallbackQuery(id=str(self.update_id + 1), from_user=self.tg, chat_instance="ci", data=data,
                           message=Message(message_id=message_id, date=datetime.now(), chat=Chat(id=self.uid, type="private"),
                                           from_user=TgUser(id=BOT_ID, is_bot=True, first_name="bot"), text="screen"))  # fmt: skip
        await self._feed(callback_query=cb)

    async def press_button(self, session: FakeSession, label_part: str) -> None:
        for b in session.buttons():
            if label_part in b.text and b.callback_data:
                await self.press(b.callback_data)
                return
        raise AssertionError(f"button containing {label_part!r} not found in {[b.text for b in session.buttons()]}")

    async def pre_checkout(self, payload: str, amount: int) -> None:
        q = PreCheckoutQuery(id="pcq", from_user=self.tg, currency="XTR", total_amount=amount, invoice_payload=payload)
        await self._feed(pre_checkout_query=q)

    async def paid(self, payload: str, amount: int, charge: str) -> None:
        sp = SuccessfulPayment(currency="XTR", total_amount=amount, invoice_payload=payload, telegram_payment_charge_id=charge,
                               provider_payment_charge_id=charge)  # fmt: skip
        await self._feed(message=self._msg(successful_payment=sp))
