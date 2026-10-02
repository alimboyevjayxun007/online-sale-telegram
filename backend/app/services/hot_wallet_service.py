from datetime import timedelta
from decimal import Decimal

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.enums import AdminRole, Direction, HotWalletTxKind
from app.core.errors import Forbidden, InvalidState, ValidationFailed
from app.core.money import D, to_nano
from app.core.timeutil import now_utc
from app.models import HotWalletTransaction
from app.providers.ton.chain import TonChainClient
from app.providers.ton.wallet import TonSigner
from app.services.audit_service import AuditService
from app.services.rate_service import RateService
from app.services.settings_service import SettingsService

log = structlog.get_logger()
NETWORK_FEE_RESERVE = Decimal("0.05")


class HotWalletService:
    def __init__(
        self,
        session: AsyncSession,
        settings: SettingsService,
        chain: TonChainClient,
        signer: TonSigner | None,
        rates: RateService,
    ) -> None:
        self.session, self.settings, self.chain, self.signer, self.rates = session, settings, chain, signer, rates

    async def address(self) -> str:
        return str(await self.settings.get("hot_wallet.address") or "")

    async def balance(self) -> Decimal:
        return await self.chain.get_balance(await self.address())

    async def withdrawable(self) -> Decimal:
        reserve = D(await self.settings.get("hot_wallet.reserve_ton"))
        return max(Decimal(0), await self.balance() - reserve - NETWORK_FEE_RESERVE)

    async def withdrawn_today(self) -> Decimal:
        start = now_utc() - timedelta(hours=24)
        total = await self.session.scalar(
            select(func.coalesce(func.sum(HotWalletTransaction.amount_ton), 0)).where(
                HotWalletTransaction.kind.in_([HotWalletTxKind.WITHDRAWAL, HotWalletTxKind.SWEEP]),
                HotWalletTransaction.created_at >= start,
            )
        )
        return D(total or 0)

    async def withdraw_to_admin(
        self, amount: Decimal, actor_id: int, role: AdminRole | None, kind: HotWalletTxKind = HotWalletTxKind.WITHDRAWAL
    ) -> str:
        """Send TON to ADMIN_TON_ADDRESS only — the destination can never be supplied by a caller."""
        if kind == HotWalletTxKind.WITHDRAWAL and role != AdminRole.OWNER:
            raise Forbidden("only the owner can withdraw")
        if await self.settings.get("hot_wallet.frozen"):
            raise InvalidState("hot wallet is frozen")
        s = get_settings()
        if not s.admin_ton_address or self.signer is None:
            raise InvalidState("ADMIN_TON_ADDRESS / signer not configured")
        if amount <= 0:
            raise ValidationFailed("amount")
        limit = D(await self.settings.get("hot_wallet.daily_withdraw_limit_ton"))
        if await self.withdrawn_today() + amount > limit:
            raise ValidationFailed("daily withdraw limit exceeded", limit=str(limit))
        if amount > await self.withdrawable():
            raise ValidationFailed("amount exceeds withdrawable balance (reserve)")
        tx_hash = await self.signer.send(s.admin_ton_address, to_nano(amount), comment=s.admin_ton_memo or None)
        rate = await self.rates.ton_usd()
        self.session.add(
            HotWalletTransaction(
                direction=Direction.OUT,
                kind=kind,
                amount_ton=amount,
                amount_usd=amount * rate,
                rate_used=rate,
                tx_hash=tx_hash if len(tx_hash) == 64 else None,
                counterparty=s.admin_ton_address,
                created_by=actor_id,
            )
        )
        await AuditService(self.session).log(
            actor_id,
            "wallet.withdraw",
            "hot_wallet",
            tx_hash,
            after={"amount_ton": str(amount), "to": s.admin_ton_address},
        )
        log.info("hot_wallet_withdraw", amount=str(amount), tx=tx_hash)
        return tx_hash

    async def auto_sweep(self) -> str | None:
        if not await self.settings.get("hot_wallet.sweep_enabled"):
            return None
        threshold = D(await self.settings.get("hot_wallet.sweep_threshold_ton"))
        extra = await self.withdrawable()
        if await self.balance() < threshold or extra <= 1:
            return None
        return await self.withdraw_to_admin(extra.quantize(Decimal("0.01")), 0, None, HotWalletTxKind.SWEEP)
