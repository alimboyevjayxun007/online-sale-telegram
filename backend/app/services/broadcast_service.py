import asyncio
from typing import Any

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import BroadcastStatus as B
from app.core.errors import InvalidState, NotFound
from app.core.timeutil import now_utc
from app.models import Broadcast, User
from app.services.notification_service import DeliveryBlocked, DeliveryRetry, Messenger

log = structlog.get_logger()
BATCH = 25


class BroadcastService:
    def __init__(self, session: AsyncSession, messenger: Messenger) -> None:
        self.session, self.m = session, messenger

    def _audience(self, segment: dict[str, Any]) -> Any:
        conds: list[Any] = [
            User.is_banned.is_(False),
            User.is_bot_blocked.is_(False),
            User.marketing_opt_out.is_(False),
        ]
        if segment.get("language"):
            conds.append(User.language.in_(segment["language"]))
        if segment.get("has_orders") is True:
            conds.append(User.orders_count > 0)
        if segment.get("has_orders") is False:
            conds.append(User.orders_count == 0)
        if segment.get("registered_after"):
            conds.append(User.created_at >= segment["registered_after"])
        if segment.get("inactive_days"):
            from datetime import timedelta

            conds.append(User.last_seen_at < now_utc() - timedelta(days=int(segment["inactive_days"])))
        if segment.get("user_ids"):
            conds.append(User.id.in_(segment["user_ids"]))
        return conds

    async def count(self, segment: dict[str, Any]) -> int:
        return (await self.session.scalar(select(func.count()).select_from(User).where(*self._audience(segment)))) or 0

    async def create(self, admin_id: int, content: dict[str, Any], segment: dict[str, Any] | None = None) -> Broadcast:
        segment = segment or {}
        b = Broadcast(
            created_by=admin_id, content=content, segment=segment, status=B.DRAFT, total=await self.count(segment)
        )
        self.session.add(b)
        await self.session.flush()
        return b

    async def get(self, bid: int) -> Broadcast:
        b = await self.session.get(Broadcast, bid)
        if b is None:
            raise NotFound("broadcast")
        return b

    async def start(self, b: Broadcast) -> Broadcast:
        if b.status not in (B.DRAFT, B.SCHEDULED, B.PAUSED):
            raise InvalidState(f"cannot start {b.status.value}")
        if b.status != B.PAUSED:
            b.total = await self.count(b.segment)
        b.status = B.RUNNING
        return b

    async def pause(self, b: Broadcast) -> Broadcast:
        if b.status != B.RUNNING:
            raise InvalidState("not running")
        b.status = B.PAUSED
        return b

    async def cancel(self, b: Broadcast) -> Broadcast:
        if b.status in (B.COMPLETED, B.CANCELLED):
            raise InvalidState("already finished")
        b.status = B.CANCELLED
        return b

    async def send_test(self, b: Broadcast, chat_id: int) -> None:
        await self.m.send_content(chat_id, b.content)

    async def activate_due(self) -> int:
        res = await self.session.execute(
            update(Broadcast)
            .where(Broadcast.status == B.SCHEDULED, Broadcast.scheduled_at <= now_utc())
            .values(status=B.RUNNING)
        )
        return int(getattr(res, "rowcount", 0) or 0)

    async def send_batch(self, b: Broadcast, size: int = BATCH) -> int:
        """Send up to ``size`` messages; returns how many users were processed. Completes when audience is exhausted."""
        if b.status != B.RUNNING:
            return 0
        users = (
            await self.session.scalars(
                select(User).where(User.id > b.cursor_user_id, *self._audience(b.segment)).order_by(User.id).limit(size)
            )
        ).all()
        if not users:
            b.status = B.COMPLETED
            return 0
        done = 0
        for u in users:
            try:
                await self.m.send_content(u.id, b.content)
                b.sent += 1
            except DeliveryBlocked:
                u.is_bot_blocked = True
                b.failed += 1
            except DeliveryRetry as r:
                log.warning("broadcast_flood_wait", seconds=r.seconds)
                await asyncio.sleep(min(r.seconds, 30))
                break  # re-send this user next batch (cursor not advanced)
            except Exception as exc:  # noqa: BLE001
                log.warning("broadcast_send_failed", user=u.id, error=str(exc))
                b.failed += 1
            b.cursor_user_id = u.id
            done += 1
        return done

    async def progress(self, b: Broadcast) -> dict[str, Any]:
        return {"id": b.id, "status": b.status.value, "total": b.total, "sent": b.sent, "failed": b.failed,
                "percent": round((b.sent + b.failed) / b.total * 100, 1) if b.total else 100.0}  # fmt: skip
