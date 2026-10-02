import asyncio
import traceback
from typing import Any

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand, BotCommandScopeChat, ErrorEvent, MenuButtonWebApp, WebAppInfo

from app.api.runtime import Runtime, Services
from app.bot.gateway import AiogramMessenger, AiogramStarsGateway
from app.bot.handlers import admin, payments, user
from app.bot.middlewares import ContextMiddleware
from app.core.config import get_settings
from app.core.db import session_maker
from app.core.redis import get_redis
from app.i18n import t

log = structlog.get_logger()

USER_COMMANDS = {
    "uz": [("start", "Botni ishga tushirish"), ("premium", "💎 Premium sotib olish"), ("stars", "⭐ Stars sotib olish"), ("wallet", "💼 Hamyon va balans"),
           ("orders", "📦 Buyurtmalarim"), ("referral", "👥 Do'stlarni taklif qilish"), ("app", "🚀 Mini ilova"), ("lang", "🌐 Til"), ("help", "🆘 Yordam"), ("cancel", "✖️ Bekor qilish")],
    "ru": [("start", "Запустить бота"), ("premium", "💎 Купить Premium"), ("stars", "⭐ Купить Stars"), ("wallet", "💼 Кошелёк и баланс"),
           ("orders", "📦 Мои заказы"), ("referral", "👥 Пригласить друзей"), ("app", "🚀 Мини-приложение"), ("lang", "🌐 Язык"), ("help", "🆘 Помощь"), ("cancel", "✖️ Отмена")],
    "en": [("start", "Start the bot"), ("premium", "💎 Buy Premium"), ("stars", "⭐ Buy Stars"), ("wallet", "💼 Wallet & balance"),
           ("orders", "📦 My orders"), ("referral", "👥 Invite friends"), ("app", "🚀 Mini app"), ("lang", "🌐 Language"), ("help", "🆘 Help"), ("cancel", "✖️ Cancel")],
}  # fmt: skip
ADMIN_COMMANDS = [("admin", "🛠 Admin panel"), ("stats", "📊 Statistika"), ("order", "🧾 Buyurtma"), ("find", "🔍 Foydalanuvchi qidirish"), ("addbalance", "➕ Balans qo'shish"),
                  ("subbalance", "➖ Balans ayirish"), ("ban", "⛔️ Bloklash"), ("unban", "✅ Blokdan chiqarish"), ("broadcast", "📣 Xabar yuborish"), ("prices", "🏷 Narxlar"),
                  ("finance", "💰 Moliya"), ("withdraw", "💸 Yechish (owner)"), ("maintenance", "🛠 Texnik ishlar on/off"), ("health", "🩺 Tizim holati")]  # fmt: skip


def create_bot() -> Bot | None:
    token = get_settings().bot_token.get_secret_value()
    if not token:
        return None
    return Bot(token, default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True))


def build_runtime(bot: Bot | None = None) -> Runtime:
    bot = bot or create_bot()
    rt = Runtime()
    settings = get_settings()
    if settings.dev_mock_provider:
        if settings.is_production:
            raise RuntimeError("DEV_MOCK_PROVIDER must never be enabled in production")
        from app.providers.fulfillment.mock import MockProvider

        rt.mock = MockProvider()
    if bot is not None:
        rt.bot = bot
        rt.messenger = AiogramMessenger(bot)
        rt.stars = AiogramStarsGateway(bot)
    return rt


def create_dispatcher(rt: Runtime) -> Dispatcher:
    dp = Dispatcher(storage=RedisStorage(get_redis(), state_ttl=1800, data_ttl=1800))
    mw = ContextMiddleware(rt)
    for observer in (dp.message, dp.callback_query, dp.pre_checkout_query):
        observer.outer_middleware(mw)
    for r in (payments.router, admin.router, user.router):
        r._parent_router = None  # module-level routers: allow several dispatchers (tests, reload)
    dp.include_routers(payments.router, admin.router, user.router)
    dp.errors.register(on_error)
    return dp


async def on_error(event: ErrorEvent, rt: Any = None) -> bool:
    exc = event.exception
    log.error("bot_handler_error", error=str(exc), trace=traceback.format_exc()[-1500:])
    update = event.update
    try:
        target = update.message or (update.callback_query.message if update.callback_query else None)
        user = (
            update.message.from_user
            if update.message
            else update.callback_query.from_user
            if update.callback_query
            else None
        )
        lang = (user.language_code or "uz")[:2] if user else "uz"
        if update.callback_query:
            await update.callback_query.answer(
                t(lang if lang in ("uz", "ru", "en") else "uz", "error_generic"), show_alert=True
            )
        elif target is not None:
            await target.answer(t(lang if lang in ("uz", "ru", "en") else "uz", "error_generic"))
        async with session_maker()() as s:
            from app.api.runtime import runtime

            await Services(s, runtime()).notifier.alert(
                f"Bot xatosi: <code>{type(exc).__name__}: {str(exc)[:200]}</code> (user {user.id if user else '-'})",
                "warn",
            )
    except Exception:  # noqa: BLE001
        pass
    return True


async def configure_bot(bot: Bot) -> None:
    """Commands (per language + admin scope), menu button and descriptions. Safe to call repeatedly."""
    s = get_settings()
    for lang, cmds in USER_COMMANDS.items():
        await bot.set_my_commands(
            [BotCommand(command=c, description=d) for c, d in cmds], language_code=None if lang == "uz" else lang
        )
    if s.owner_telegram_id:
        admin_cmds = [BotCommand(command=c, description=d) for c, d in USER_COMMANDS["uz"] + ADMIN_COMMANDS]
        await bot.set_my_commands(admin_cmds, scope=BotCommandScopeChat(chat_id=s.owner_telegram_id))
    if s.webapp_url.startswith("https://"):
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="🚀 Ilova", web_app=WebAppInfo(url=s.webapp_url))
        )
    desc = {
        "uz": (
            "💎 Telegram Premium va ⭐ Stars — eng arzon narxda. 1–3 daqiqada faollashadi.",
            "Premium va Stars eng arzon narxda · TON · Stars · 24/7",
        ),
        "ru": (
            "💎 Telegram Premium и ⭐ Stars по лучшей цене. Активация за 1–3 минуты.",
            "Premium и Stars по лучшей цене · TON · Stars · 24/7",
        ),
        "en": (
            "💎 Telegram Premium and ⭐ Stars at the lowest price. Activated in 1–3 minutes.",
            "Premium and Stars at the lowest price · TON · Stars · 24/7",
        ),
    }
    for lang, (d, about) in desc.items():
        code = None if lang == "uz" else lang
        await bot.set_my_description(d, language_code=code)
        await bot.set_my_short_description(about, language_code=code)


async def set_webhook(bot: Bot) -> None:
    s = get_settings()
    await bot.set_webhook(
        url=s.public_base_url.rstrip("/") + "/tg/webhook",
        secret_token=s.webhook_secret.get_secret_value() or None,
        allowed_updates=["message", "callback_query", "pre_checkout_query", "my_chat_member"],
        drop_pending_updates=False,
    )


async def run_polling() -> None:
    """Development mode: long polling (no domain / HTTPS needed)."""
    from app.core.logging import setup_logging

    setup_logging()
    rt = build_runtime()
    if rt.bot is None:
        raise SystemExit("BOT_TOKEN is empty")
    from app.api.runtime import set_runtime

    set_runtime(rt)
    dp = create_dispatcher(rt)
    await rt.bot.delete_webhook()
    await configure_bot(rt.bot)
    log.info("polling_started")
    await dp.start_polling(rt.bot, allowed_updates=["message", "callback_query", "pre_checkout_query"])


if __name__ == "__main__":
    asyncio.run(run_polling())
