from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import BalanceTxType
from app.core.errors import InsufficientBalance, NotFound, ValidationFailed
from app.core.money import quantize
from app.models import BalanceTransaction, User


class BalanceService:
    """Internal USD balance. Every change is a ledger row; the user row is locked first."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _lock(self, user_id: int) -> User:
        user = await self.session.scalar(select(User).where(User.id == user_id).with_for_update())
        if user is None:
            raise NotFound("user")
        return user

    async def credit(
        self,
        user_id: int,
        amount: Decimal,
        type_: BalanceTxType,
        ref_type: str | None = None,
        ref_id: int | None = None,
        comment: str | None = None,
        created_by: int | None = None,
    ) -> BalanceTransaction:
        amount = quantize(amount)
        if amount <= 0:
            raise ValidationFailed("amount must be positive")
        user = await self._lock(user_id)
        user.balance_usd = quantize(user.balance_usd + amount)
        return await self._write(user, amount, type_, ref_type, ref_id, comment, created_by)

    async def debit(
        self,
        user_id: int,
        amount: Decimal,
        type_: BalanceTxType,
        ref_type: str | None = None,
        ref_id: int | None = None,
        comment: str | None = None,
        created_by: int | None = None,
    ) -> BalanceTransaction:
        amount = quantize(amount)
        if amount <= 0:
            raise ValidationFailed("amount must be positive")
        user = await self._lock(user_id)
        if user.balance_usd < amount:
            raise InsufficientBalance(need_usd=str(amount - user.balance_usd))
        user.balance_usd = quantize(user.balance_usd - amount)
        return await self._write(user, -amount, type_, ref_type, ref_id, comment, created_by)

    async def _write(
        self,
        user: User,
        signed: Decimal,
        type_: BalanceTxType,
        ref_type: str | None,
        ref_id: int | None,
        comment: str | None,
        created_by: int | None,
    ) -> BalanceTransaction:
        tx = BalanceTransaction(
            user_id=user.id,
            amount_usd=signed,
            balance_after=user.balance_usd,
            type=type_,
            ref_type=ref_type,
            ref_id=ref_id,
            comment=comment,
            created_by=created_by,
        )
        self.session.add(tx)
        await self.session.flush()
        return tx

    async def history(self, user_id: int, limit: int = 20, offset: int = 0) -> list[BalanceTransaction]:
        stmt = (
            select(BalanceTransaction)
            .where(BalanceTransaction.user_id == user_id)
            .order_by(BalanceTransaction.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list((await self.session.scalars(stmt)).all())
