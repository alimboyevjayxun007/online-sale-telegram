from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.enums import AdminRole, BalanceTxType, ExpenseCategory, ProductScope, PromoType
from app.core.errors import Forbidden, NotFound, ValidationFailed
from app.core.money import D, quantize
from app.core.timeutil import now_utc
from app.models import Admin, Channel, Expense, PremiumPlan, PromoCode, StarPackage, UnmatchedTonTx, User
from app.providers.fulfillment.base import FulfillmentProvider
from app.services.audit_service import AuditService
from app.services.balance_service import BalanceService
from app.services.notification_service import NotificationService
from app.services.settings_service import SettingsService
from app.services.user_service import UserService


class AdminService:
    def __init__(
        self, session: AsyncSession, settings: SettingsService, notifier: NotificationService | None = None
    ) -> None:
        self.session, self.settings, self.notifier = session, settings, notifier
        self.audit = AuditService(session)
        self.users = UserService(session)

    # ----- admins -----
    async def list_admins(self) -> list[dict[str, Any]]:
        rows = (await self.session.scalars(select(Admin).order_by(Admin.created_at))).all()
        out = [
            {"user_id": a.user_id, "role": a.role.value} for a in rows if a.user_id != get_settings().owner_telegram_id
        ]
        return [{"user_id": get_settings().owner_telegram_id, "role": "owner"}] + out

    async def add_admin(self, actor: int, user_id: int, role: AdminRole) -> Admin:
        if role == AdminRole.OWNER:
            raise Forbidden("owner role is configured in .env only")
        if user_id == get_settings().owner_telegram_id:
            raise ValidationFailed("already owner")
        if await self.session.get(User, user_id) is None:
            raise NotFound("user must have started the bot first")
        admin = await self.session.get(Admin, user_id)
        before = admin.role.value if admin else None
        if admin is None:
            admin = Admin(user_id=user_id, role=role, added_by=actor)
            self.session.add(admin)
        else:
            admin.role = role
        await self.audit.log(actor, "admin.set", "admin", user_id, before, role.value)
        return admin

    async def remove_admin(self, actor: int, user_id: int) -> None:
        admin = await self.session.get(Admin, user_id)
        if admin is None or user_id == get_settings().owner_telegram_id:
            raise NotFound("admin")
        await self.session.delete(admin)
        await self.session.flush()
        await self.audit.log(actor, "admin.remove", "admin", user_id, admin.role.value, None)

    # ----- users -----
    async def adjust_balance(
        self, actor: int, role: AdminRole, user_id: int, amount: Decimal, comment: str | None
    ) -> Decimal:
        limit = D(await self.settings.get("admin.balance_limit_usd"))
        if role != AdminRole.OWNER and abs(amount) > limit:
            raise Forbidden(f"admins can adjust at most {limit} $", limit=str(limit))
        if amount == 0:
            raise ValidationFailed("amount")
        bal = BalanceService(self.session)
        if amount > 0:
            tx = await bal.credit(user_id, amount, BalanceTxType.ADMIN_CREDIT, "admin", actor, comment, actor)
        else:
            tx = await bal.debit(user_id, -amount, BalanceTxType.ADMIN_DEBIT, "admin", actor, comment, actor)
        await self.audit.log(
            actor, "balance.adjust", "user", user_id, None, {"amount": str(amount), "comment": comment}
        )
        return tx.balance_after

    async def ban(self, actor: int, user_id: int, reason: str | None) -> None:
        if user_id == get_settings().owner_telegram_id:
            raise Forbidden("cannot ban owner")
        await self.users.ban(user_id, reason)
        await self.audit.log(actor, "user.ban", "user", user_id, None, {"reason": reason})

    async def unban(self, actor: int, user_id: int) -> None:
        await self.users.unban(user_id)
        await self.audit.log(actor, "user.unban", "user", user_id)

    # ----- pricing -----
    async def update_plan(self, actor: int, plan_id: int, **fields: Any) -> PremiumPlan:
        plan = await self.session.get(PremiumPlan, plan_id)
        if plan is None:
            raise NotFound("plan")
        allowed = {"is_enabled", "markup_percent", "fixed_markup_usd", "fixed_price_usd", "price_stars", "badge",
                   "reference_price_usd", "cost_ton", "provider_supported"}  # fmt: skip
        before = {k: str(getattr(plan, k)) for k in fields if k in allowed}
        for k, v in fields.items():
            if k not in allowed:
                raise ValidationFailed(f"field {k}")
            if (
                k in ("markup_percent", "fixed_markup_usd", "fixed_price_usd", "reference_price_usd", "cost_ton")
                and v is not None
            ):
                v = D(v)
                if v < 0:
                    raise ValidationFailed(k)
            setattr(plan, k, v)
        if plan.months == 1 and plan.is_enabled and not plan.provider_supported:
            raise ValidationFailed("1-month gifts are not supported by Telegram yet; set provider_supported first")
        await self.audit.log(actor, "price.update", "plan", plan_id, before, {k: str(v) for k, v in fields.items()})
        return plan

    async def set_star_packages(self, actor: int, packages: list[dict[str, Any]]) -> None:
        existing = {p.amount: p for p in (await self.session.scalars(select(StarPackage))).all()}
        seen: set[int] = set()
        for i, item in enumerate(packages):
            amount = int(item["amount"])
            if amount < 50:
                raise ValidationFailed("minimum package is 50 stars")
            seen.add(amount)
            pkg = existing.get(amount) or StarPackage(amount=amount)
            pkg.is_enabled, pkg.is_popular, pkg.sort_order = (
                bool(item.get("enabled", True)),
                bool(item.get("popular", False)),
                i,
            )
            self.session.add(pkg)
        for amount, pkg in existing.items():
            if amount not in seen:
                pkg.is_enabled = False
        await self.audit.log(actor, "price.packages", "star_packages", None, None, [int(p["amount"]) for p in packages])

    async def refresh_provider_prices(self, providers: list[FulfillmentProvider]) -> int:
        changed = 0
        plans = {p.months: p for p in (await self.session.scalars(select(PremiumPlan))).all()}
        for provider in providers:
            try:
                prices = await provider.get_prices()
            except Exception:  # noqa: BLE001 - provider down, keep old prices
                continue
            for months, cost in prices.premium_ton.items():
                if months in plans:
                    plans[months].cost_ton, plans[months].cost_updated_at = cost, now_utc()
                    changed += 1
            if prices.star_unit_ton:
                await self.settings.set("provider.star_unit_cost_ton", str(prices.star_unit_ton))
                changed += 1
            if changed:
                break
        return changed

    # ----- promo / expenses / channels / unmatched -----
    async def create_promo(self, actor: int, code: str, type_: PromoType, value: Decimal, **kw: Any) -> PromoCode:
        code = code.strip().upper()
        if not code.isalnum() or not 3 <= len(code) <= 32:
            raise ValidationFailed("code must be 3-32 letters/digits")
        if value <= 0 or (type_ == PromoType.PERCENT and value > 90):
            raise ValidationFailed("value")
        promo = PromoCode(code=code, type=type_, value=value, applies_to=kw.pop("applies_to", ProductScope.ALL), **kw)
        self.session.add(promo)
        await self.session.flush()
        await self.audit.log(actor, "promo.create", "promo", promo.id, None, {"code": code, "value": str(value)})
        return promo

    async def add_expense(
        self, actor: int, category: ExpenseCategory, amount: Decimal, note: str | None, spent_on: date | None = None
    ) -> Expense:
        if amount <= 0:
            raise ValidationFailed("amount")
        from app.core.timeutil import today_local

        e = Expense(
            category=category,
            amount_usd=quantize(amount),
            note=note,
            spent_on=spent_on or today_local(),
            created_by=actor,
        )
        self.session.add(e)
        await self.audit.log(
            actor, "expense.add", "expense", None, None, {"amount": str(amount), "category": category.value}
        )
        return e

    async def add_channel(self, actor: int, chat_id: int, title: str, invite_link: str | None) -> Channel:
        ch = Channel(chat_id=chat_id, title=title, invite_link=invite_link)
        self.session.add(ch)
        await self.audit.log(actor, "channel.add", "channel", chat_id)
        return ch

    async def resolve_unmatched(self, actor: int, row_id: int, user_id: int | None, rate: Decimal) -> UnmatchedTonTx:
        row = await self.session.get(UnmatchedTonTx, row_id)
        if row is None or row.resolution != "pending":
            raise NotFound("unmatched tx")
        if user_id is None:
            row.resolution = "ignored"
        else:
            await BalanceService(self.session).credit(
                user_id,
                quantize(row.amount_ton * rate),
                BalanceTxType.ADMIN_CREDIT,
                "unmatched_tx",
                row.id,
                "manual match",
                actor,
            )
            row.resolution = f"credited:{user_id}"
        row.resolved_by = actor
        await self.audit.log(actor, "unmatched.resolve", "unmatched_ton_tx", row_id, None, row.resolution)
        return row
