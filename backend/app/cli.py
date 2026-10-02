import asyncio
from collections.abc import Coroutine
from pathlib import Path
from typing import Any

import typer

app = typer.Typer(no_args_is_help=True, help="Soft-tg-Market management commands")
wallet_app = typer.Typer(help="Hot wallet")
bot_app = typer.Typer(help="Telegram bot")
db_app = typer.Typer(help="Database")
stats_app = typer.Typer(help="Statistics")
app.add_typer(wallet_app, name="wallet")
app.add_typer(bot_app, name="bot")
app.add_typer(db_app, name="db")
app.add_typer(stats_app, name="stats")


def run(coro: Coroutine[Any, Any, Any]) -> None:
    asyncio.run(coro)


@wallet_app.command("generate")
def wallet_generate(force: bool = typer.Option(False, "--force", help="Overwrite an existing wallet file")) -> None:
    """Create the hot wallet ON THIS SERVER. The 24 words are shown once — write them on paper."""
    from app.core.config import get_settings
    from app.providers.ton.wallet import generate_wallet_file

    s = get_settings()
    path = Path(s.hot_wallet_mnemonic_file or "")
    if not s.hot_wallet_mnemonic_file or not s.encryption_key.get_secret_value():
        typer.echo("Set HOT_WALLET_MNEMONIC_FILE and ENCRYPTION_KEY first", err=True)
        raise typer.Exit(1)
    if path.exists() and not force:
        typer.echo(f"{path} already exists (use --force only if you are sure: the old seed will be lost!)", err=True)
        raise typer.Exit(1)
    address, words = generate_wallet_file()

    async def save() -> None:
        from app.core.db import dispose_engine, session_maker
        from app.services.settings_service import SettingsService

        async with session_maker()() as session:
            await SettingsService(session).set("hot_wallet.address", address)
            await session.commit()
        await dispose_engine()

    run(save())
    typer.echo(f"\nHot wallet address: {address}\n")
    typer.echo("WRITE THESE 24 WORDS ON PAPER AND KEEP THEM SAFE (shown only once):\n")
    typer.echo(" ".join(words))
    typer.echo("\nSend a small amount of TON to the address above (e.g. 35 TON: 30 reserve + fees).")


@wallet_app.command("info")
def wallet_info() -> None:
    async def go() -> None:
        from app.api.runtime import Services
        from app.core.db import dispose_engine, session_maker

        async with session_maker()() as session:
            svc = Services(session)
            addr = await svc.settings.get("hot_wallet.address")
            typer.echo(f"address: {addr}")
            if addr:
                typer.echo(f"balance: {await svc.hot_wallet().balance()} TON")
        await dispose_engine()

    run(go())


@bot_app.command("set-webhook")
def bot_set_webhook() -> None:
    """Webhook + commands + menu button + descriptions."""

    async def go() -> None:
        from app.bot.setup import configure_bot, create_bot, set_webhook

        bot = create_bot()
        if bot is None:
            typer.echo("BOT_TOKEN is empty", err=True)
        raise typer.Exit(1)
        await configure_bot(bot)
        await set_webhook(bot)
        info = await bot.get_webhook_info()
        typer.echo(f"webhook: {info.url}")
        await bot.session.close()

    run(go())


@bot_app.command("poll")
def bot_poll() -> None:
    """Development: run the bot with long polling."""
    from app.bot.setup import run_polling

    run(run_polling())


@bot_app.command("detect-chat-id")
def bot_detect_chat() -> None:
    typer.echo("Add the bot to your log channel/group as admin, send any message there and open:\n"
               "https://api.telegram.org/bot<TOKEN>/getUpdates  → find chat.id (starts with -100).")  # fmt: skip


@db_app.command("seed-owner")
def db_seed_owner() -> None:
    async def go() -> None:
        from app.core.db import dispose_engine, session_maker
        from app.services.user_service import UserService

        async with session_maker()() as session:
            await UserService(session).ensure_owner()
            await session.commit()
        await dispose_engine()
        typer.echo("owner ensured")

    run(go())


@stats_app.command("recompute")
def stats_recompute(frm: str, to: str) -> None:
    async def go() -> None:
        from datetime import date, timedelta

        from app.core.db import dispose_engine, session_maker
        from app.services.analytics_service import AnalyticsService

        d, end = date.fromisoformat(frm), date.fromisoformat(to)
        async with session_maker()() as session:
            a = AnalyticsService(session)
            while d <= end:
                await a.compute_day(d)
                d += timedelta(days=1)
            await session.commit()
        await dispose_engine()

    run(go())


@app.command("gen-keys")
def gen_keys() -> None:
    """Generate APP_SECRET_KEY, ENCRYPTION_KEY, WEBHOOK_SECRET (paste into .env)."""
    import secrets

    from cryptography.fernet import Fernet

    typer.echo(f"APP_SECRET_KEY={secrets.token_hex(32)}")
    typer.echo(f"ENCRYPTION_KEY={Fernet.generate_key().decode()}")
    typer.echo(f"WEBHOOK_SECRET={secrets.token_hex(32)}")


@app.command("dev-mock")
def dev_mock() -> None:
    """Print a signed initData string for local Mini App development (needs BOT_TOKEN)."""
    from app.core.config import get_settings
    from app.core.security import build_init_data

    s = get_settings()
    uid = s.owner_telegram_id or 1
    typer.echo(
        build_init_data(
            {"id": uid, "first_name": "Dev", "username": "dev", "language_code": "uz"}, s.bot_token.get_secret_value()
        )
    )


if __name__ == "__main__":
    app()
