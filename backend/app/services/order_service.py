from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import OrderStatus as S
from app.core.errors import InvalidState, NotFound
from app.core.timeutil import now_utc
from app.models import Order, OrderEvent

ALLOWED_TRANSITIONS: dict[S, set[S]] = {
    S.AWAITING_PAYMENT: {S.PAID, S.EXPIRED, S.CANCELLED},
    S.PAID: {S.PROCESSING, S.REFUNDED},
    S.PROCESSING: {S.COMPLETED, S.PAID, S.FAILED, S.NEEDS_REVIEW},
    S.NEEDS_REVIEW: {S.COMPLETED, S.PAID, S.REFUNDED, S.FAILED},
    S.FAILED: {S.PAID, S.REFUNDED, S.COMPLETED},
    S.COMPLETED: set(),
    S.REFUNDED: set(),
    S.EXPIRED: set(),
    S.CANCELLED: set(),
}


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, order_id: int) -> Order:
        order = await self.session.get(Order, order_id)
        if order is None:
            raise NotFound("order")
        return order

    async def by_public_id(self, public_id: str, user_id: int | None = None) -> Order:
        stmt = select(Order).where(Order.public_id == public_id.upper())
        if user_id is not None:
            stmt = stmt.where(Order.user_id == user_id)
        order = await self.session.scalar(stmt)
        if order is None:
            raise NotFound("order")
        return order

    async def transition(
        self, order: Order, to: S, actor: str = "system", expect: S | None = None, **fields: Any
    ) -> Order:
        """Atomic compare-and-set status change (UPDATE ... WHERE status = :old) + audit event."""
        old = expect or order.status
        if to not in ALLOWED_TRANSITIONS[old]:
            raise InvalidState(f"{old.value} -> {to.value} is not allowed")
        res = await self.session.execute(
            update(Order).where(Order.id == order.id, Order.status == old).values(status=to, **fields)
        )
        if getattr(res, "rowcount", 0) == 0:
            raise InvalidState(f"order {order.public_id} is no longer {old.value}")
        self.session.add(
            OrderEvent(
                order_id=order.id,
                from_status=old,
                to_status=to,
                actor=actor,
                data={k: str(v) for k, v in fields.items() if k in ("error_code", "provider", "attempts")},
            )
        )
        await self.session.flush()
        await self.session.refresh(order)
        return order

    async def mark_paid(self, order: Order, actor: str = "system") -> Order:
        return await self.transition(order, S.PAID, actor, paid_at=now_utc(), next_attempt_at=None)

    async def list_for_user(
        self, user_id: int, status: list[S] | None = None, limit: int = 20, offset: int = 0
    ) -> list[Order]:
        stmt = select(Order).where(Order.user_id == user_id)
        if status:
            stmt = stmt.where(Order.status.in_(status))
        stmt = stmt.order_by(Order.id.desc()).limit(limit).offset(offset)
        return list((await self.session.scalars(stmt)).all())

    async def events(self, order_id: int) -> list[OrderEvent]:
        stmt = select(OrderEvent).where(OrderEvent.order_id == order_id).order_by(OrderEvent.id)
        return list((await self.session.scalars(stmt)).all())
