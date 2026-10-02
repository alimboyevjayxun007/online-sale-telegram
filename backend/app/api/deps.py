from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_session
from app.core.enums import AdminRole
from app.core.errors import Forbidden, InvalidInitData, UserBanned
from app.core.security import parse_init_user, validate_init_data
from app.models import User
from app.services.user_service import UserService

Session = Annotated[AsyncSession, Depends(get_session)]
RANK = {AdminRole.SUPPORT: 1, AdminRole.ADMIN: 2, AdminRole.OWNER: 3}


async def current_user(session: Session, authorization: Annotated[str | None, Header()] = None) -> User:
    if not authorization or not authorization.startswith("tma "):
        raise InvalidInitData()
    pairs = validate_init_data(authorization[4:], get_settings().bot_token.get_secret_value())
    info = parse_init_user(pairs)

    def opt(key: str) -> str | None:
        v = info.get(key)
        return str(v) if v else None

    user, _ = await UserService(session).upsert_from_telegram(
        int(info["id"]),
        opt("username"),
        opt("first_name"),
        opt("last_name"),
        opt("language_code"),
        bool(info.get("is_premium")),
    )
    if user.is_banned:
        raise UserBanned()
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def require_role(minimum: AdminRole) -> Callable[..., Awaitable[User]]:
    async def dep(user: CurrentUser, session: Session) -> User:
        role = await UserService(session).role_of(user.id)
        if role is None or RANK[role] < RANK[minimum]:
            raise Forbidden()
        user.__dict__["_role"] = role
        return user

    return dep
