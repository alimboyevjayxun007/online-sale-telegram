from typing import Annotated

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, Header, HTTPException, Request

from app.core.config import get_settings

router = APIRouter()


@router.post("/tg/webhook")
async def telegram_webhook(
    request: Request, x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None
) -> dict[str, bool]:
    secret = get_settings().webhook_secret.get_secret_value()
    if not secret or x_telegram_bot_api_secret_token != secret:
        raise HTTPException(status_code=401)
    bot: Bot | None = getattr(request.app.state, "bot", None)
    dp: Dispatcher | None = getattr(request.app.state, "dp", None)
    if bot is None or dp is None:
        raise HTTPException(status_code=503)
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}
