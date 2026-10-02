from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.enums import AdminRole
from app.core.errors import NotFound, ValidationFailed
from app.core.timeutil import now_utc, today_local
from app.models import Admin, User, UserDailyActivity

LANGS = {"uz", "ru", "en"}


def pick_language(code: str | None) -> str:
    code = (code or "uz")[:2].lower()
    return code if code in LANGS else "uz"


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_from_telegram(
        self,
        tg_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None = None,
        language_code: str | None = None,
        is_premium: bool = False,
        referrer_id: int | None = None,
        source: str | None = None,
    ) -> tuple[User, bool]:
        """Create or update; returns (user, created). Referrer/source set only on creation."""
        user = await self.session.get(User, tg_id)
        if user is None:
            if referrer_id == tg_id or (referrer_id is not None and await self.session.get(User, referrer_id) is None):
                referrer_id = None
            user = User(
                id=tg_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language=pick_language(language_code),
                tg_is_premium=is_premium,
                referrer_id=referrer_id,
                source=source,
            )
            self.session.add(user)
            await self.session.flush()
            created = True
        else:
            user.username, user.first_name, user.last_name = username, first_name, last_name
            user.tg_is_premium = is_premium
            user.last_seen_at = now_utc()
            created = False
        await self.touch_activity(tg_id)
        return user, created

    async def touch_activity(self, user_id: int) -> None:
        await self.session.execute(
            insert(UserDailyActivity).values(day=today_local(), user_id=user_id).on_conflict_do_nothing()
        )

    async def get(self, user_id: int) -> User:
        user = await self.session.get(User, user_id)
        if user is None:
            raise NotFound("user")
        return user

    async def set_language(self, user: User, lang: str) -> None:
        if lang not in LANGS:
            raise ValidationFailed("language")
        user.language = lang

    async def ban(self, user_id: int, reason: str | None = None) -> User:
        user = await self.get(user_id)
        user.is_banned, user.ban_reason = True, reason
        return user

    async def unban(self, user_id: int) -> User:
        user = await self.get(user_id)
        user.is_banned, user.ban_reason = False, None
        return user

    async def role_of(self, user_id: int) -> AdminRole | None:
        if user_id == get_settings().owner_telegram_id:
            return AdminRole.OWNER
        admin = await self.session.get(Admin, user_id)
        if admin is None or admin.role == AdminRole.OWNER:
            return None  # owner role only comes from .env
        return admin.role

    async def search(self, q: str, limit: int = 20) -> list[User]:
        q = q.strip().lstrip("@")
        cond: list[ColumnElement[bool]] = [
            func.lower(User.username).like(f"%{q.lower()}%"),
            User.first_name.ilike(f"%{q}%"),
        ]
        if q.isdigit():
            cond.append(User.id == int(q))
        stmt = select(User).where(or_(*cond)).order_by(User.created_at.desc()).limit(limit)
        return list((await self.session.scalars(stmt)).all())

    async def ensure_owner(self) -> None:
        owner_id = get_settings().owner_telegram_id
        if not owner_id:
            return
        await self.upsert_from_telegram(owner_id, None, "Owner")
        await self.session.execute(
            insert(Admin)
            .values(user_id=owner_id, role=AdminRole.OWNER)
            .on_conflict_do_update(index_elements=["user_id"], set_={"role": AdminRole.OWNER})
        )
