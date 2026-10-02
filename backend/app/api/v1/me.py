from decimal import Decimal

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import CurrentUser, Session
from app.core.config import get_settings
from app.core.money import quantize
from app.core.redis import get_redis
from app.services.rate_service import RateService
from app.services.user_service import UserService

router = APIRouter(tags=["me"])


class LanguageIn(BaseModel):
    language: str


def money(v: Decimal) -> str:
    return str(quantize(v))


@router.get("/me")
async def get_me(user: CurrentUser, session: Session) -> dict[str, object]:
    role = await UserService(session).role_of(user.id)
    rates = RateService(session, get_redis())
    usd_uzs, ton_usd = await rates.usd_uzs(), await rates.ton_usd()
    s = get_settings()
    return {
        "id": user.id,
        "name": user.first_name,
        "username": user.username,
        "language": user.language,
        "balance_usd": money(user.balance_usd),
        "balance_uzs": int(user.balance_usd * usd_uzs),
        "balance_ton": money(user.balance_usd / ton_usd),
        "is_admin": role is not None,
        "role": role.value if role else None,
        "ref_link": f"https://t.me/{s.bot_username}?start=ref_{user.id}" if s.bot_username else None,
    }


@router.patch("/me")
async def patch_me(body: LanguageIn, user: CurrentUser, session: Session) -> dict[str, str]:
    await UserService(session).set_language(user, body.language)
    return {"language": user.language}
