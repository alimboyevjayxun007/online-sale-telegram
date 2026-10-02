from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from aiogram import BaseMiddleware, Bot
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery, TelegramObject
from sqlalchemy import select

from app.api.runtime import Runtime, Services
from app.core.config import get_settings
from app.core.db import session_maker
from app.core.redis import get_redis
from app.i18n import t
from app.models import Channel
from app.services.user_service import UserService

log = structlog.get_logger()


def _from_user(event: TelegramObject) -> Any:
    return getattr(event, "from_user", None)


class ContextMiddleware(BaseMiddleware):
    """throttle → DB session → user upsert → ban → maintenance → mandatory subscription."""

    def __init__(self, rt: Runtime) -> None:
        self.rt = rt

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg = _from_user(event)
        if tg is None or tg.is_bot:
            return None
        is_payment = isinstance(event, PreCheckoutQuery) or (
            isinstance(event, Message) and (event.successful_payment or event.refunded_payment)
        )
        redis = get_redis()
        throttle = get_settings().throttle_ms
        if throttle and not is_payment and not await redis.set(f"thr:{tg.id}", "1", px=throttle, nx=True):
            if isinstance(event, CallbackQuery):
                await event.answer("⏳")
            return None
        async with session_maker()() as session:
            svc = Services(session, self.rt)
            users = UserService(session)
            ref_id = source = None
            if isinstance(event, Message) and event.text and event.text.startswith("/start "):
                arg = event.text.split(maxsplit=1)[1].strip()
                if arg.startswith("ref_") and arg[4:].isdigit():
                    ref_id = int(arg[4:])
                elif arg.startswith("src_"):
                    source = arg[:64]
            user, created = await users.upsert_from_telegram(
                tg.id,
                tg.username,
                tg.first_name,
                tg.last_name,
                tg.language_code,
                bool(getattr(tg, "is_premium", False)),
                ref_id,
                source,
            )
            role = await users.role_of(tg.id)
            data.update(session=session, svc=svc, user=user, lang=user.language, created=created, role=role, rt=self.rt)
            if not is_payment:
                blocked = await self._gate(event, data, svc, role)
                if blocked:
                    await session.commit()
                    return None
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise

    async def _gate(self, event: TelegramObject, data: dict[str, Any], svc: Services, role: Any) -> bool:
        user, lang, session = data["user"], data["lang"], data["session"]
        if user.is_banned:
            support = await svc.settings.get("bot.support_username") or ""
            await self._say(event, t(lang, "banned", support=f"@{support}" if support else ""))
            return True
        if role is not None:
            return False
        if await svc.settings.get("bot.maintenance"):
            await self._say(event, t(lang, "maintenance"))
            return True
        if await svc.settings.get("bot.mandatory_subscription"):
            chans = (await session.scalars(select(Channel).where(Channel.is_active.is_(True)))).all()
            if chans and not await self._subscribed(chans, user.id):
                from app.bot.callbacks import Menu
                from app.bot.keyboards import btn, kb

                rows = [btn(f"➕ {c.title}", url=c.invite_link, style="primary") for c in chans if c.invite_link]
                markup = kb(*rows, btn(t(lang, "b_sub_check"), Menu(a="subcheck"), style="success"))
                if isinstance(event, CallbackQuery) and event.data == Menu(a="subcheck").pack():
                    await event.answer(t(lang, "not_subscribed"), show_alert=True)
                else:
                    await self._say(event, t(lang, "need_subscription"), markup)
                return True
        return False

    async def _subscribed(self, chans: Any, user_id: int) -> bool:
        redis = get_redis()
        cached = await redis.get(f"sub:{user_id}")
        if cached is not None:
            return cached == "1"
        bot: Bot | None = self.rt.bot
        if bot is None:
            return True
        ok = True
        for c in chans:
            try:
                m = await bot.get_chat_member(c.chat_id, user_id)
                if m.status in ("left", "kicked"):
                    ok = False
            except Exception as exc:  # noqa: BLE001 - if the bot cannot check, do not lock users out
                log.warning("subscription_check_failed", chat=c.chat_id, error=str(exc))
        await redis.set(f"sub:{user_id}", "1" if ok else "0", ex=300 if ok else 20)
        return ok

    async def _say(self, event: TelegramObject, text: str, markup: Any = None) -> None:
        if isinstance(event, CallbackQuery):
            await event.answer()
            if isinstance(event.message, Message):
                await event.message.answer(text, reply_markup=markup)
        elif isinstance(event, Message):
            await event.answer(text, reply_markup=markup)
        elif isinstance(event, PreCheckoutQuery):
            await event.answer(ok=False, error_message=text[:200])
