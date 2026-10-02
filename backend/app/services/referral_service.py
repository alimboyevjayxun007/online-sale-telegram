from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import BalanceTxType, RewardStatus
from app.core.money import D, quantize
from app.models import Order, ReferralReward, User
from app.services.balance_service import BalanceService
from app.services.notification_service import NotificationService
from app.services.settings_service import SettingsService


class ReferralService:
    def __init__(self, session: AsyncSession, settings: SettingsService, notifier: NotificationService) -> None:
        self.session, self.settings, self.notifier = session, settings, notifier
        self.balance = BalanceService(session)

    async def reward_for_order(self, order: Order) -> Decimal | None:
        if not await self.settings.get("referral.enabled"):
            return None
        buyer = await self.session.get(User, order.user_id)
        if buyer is None or buyer.referrer_id is None:
            return None
        if await self.session.scalar(select(ReferralReward.id).where(ReferralReward.order_id == order.id)):
            return None
        amount = quantize(order.price_usd * D(await self.settings.get("referral.percent")) / 100)
        if amount <= 0:
            return None
        self.session.add(
            ReferralReward(
                referrer_id=buyer.referrer_id,
                referred_id=buyer.id,
                order_id=order.id,
                amount_usd=amount,
                status=RewardStatus.CREDITED,
            )
        )
        await self.balance.credit(buyer.referrer_id, amount, BalanceTxType.REFERRAL_BONUS, "order", order.id)
        referrer = await self.session.get(User, buyer.referrer_id)
        if referrer is not None:
            await self.notifier.notify_user(referrer, "referral_bonus", amount=f"{amount:.2f} $")
        return amount

    async def revoke_for_order(self, order: Order) -> None:
        reward = await self.session.scalar(select(ReferralReward).where(ReferralReward.order_id == order.id))
        if reward is None or reward.status != RewardStatus.CREDITED:
            return
        referrer = await self.session.get(User, reward.referrer_id)
        take = min(reward.amount_usd, referrer.balance_usd if referrer else Decimal(0))
        if take > 0:
            await self.balance.debit(reward.referrer_id, take, BalanceTxType.REFERRAL_REVOKE, "order", order.id)
        reward.status = RewardStatus.REVOKED

    async def stats(self, user_id: int) -> dict[str, object]:
        from sqlalchemy import func

        invited = await self.session.scalar(select(func.count()).select_from(User).where(User.referrer_id == user_id))
        earned = await self.session.scalar(
            select(func.coalesce(func.sum(ReferralReward.amount_usd), 0)).where(
                ReferralReward.referrer_id == user_id, ReferralReward.status == RewardStatus.CREDITED
            )
        )
        return {"invited": invited or 0, "earned_usd": str(quantize(D(earned or 0)))}
