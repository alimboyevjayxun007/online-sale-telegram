"""ORM models. Money: USD NUMERIC(18,6), TON NUMERIC(20,9), Stars INTEGER."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

import sqlalchemy as sa
from sqlalchemy import BigInteger, ForeignKey, Index, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core import enums as e
from app.core.db import Base

USD = Numeric(18, 6)
TON = Numeric(20, 9)
BIG = Numeric(30, 9)
TS = sa.DateTime(timezone=True)


def pg_enum(cls: type[Enum]) -> sa.Enum:
    return sa.Enum(cls, name=cls.__name__.lower(), values_callable=lambda c: [m.value for m in c])


NOW = text("now()")


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    username: Mapped[str | None] = mapped_column(String(32))
    first_name: Mapped[str | None] = mapped_column(String(128))
    last_name: Mapped[str | None] = mapped_column(String(128))
    language: Mapped[str] = mapped_column(String(5), default="uz", server_default="uz")
    balance_usd: Mapped[Decimal] = mapped_column(USD, default=Decimal(0), server_default="0")
    referrer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    is_banned: Mapped[bool] = mapped_column(default=False, server_default="false")
    ban_reason: Mapped[str | None] = mapped_column(String(255))
    is_bot_blocked: Mapped[bool] = mapped_column(default=False, server_default="false")
    marketing_opt_out: Mapped[bool] = mapped_column(default=False, server_default="false")
    tg_is_premium: Mapped[bool] = mapped_column(default=False, server_default="false")
    source: Mapped[str | None] = mapped_column(String(64))
    total_spent_usd: Mapped[Decimal] = mapped_column(USD, default=Decimal(0), server_default="0")
    orders_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(TS, server_default=NOW)
    last_seen_at: Mapped[datetime] = mapped_column(TS, server_default=NOW)
    __table_args__ = (
        sa.CheckConstraint("balance_usd >= 0", name="ck_users_balance_nonneg"),
        sa.CheckConstraint("referrer_id <> id", name="ck_users_not_self_referrer"),
        Index("ix_users_username_lower", sa.func.lower(sa.column("username"))),
        Index("ix_users_created_at", "created_at"),
        Index("ix_users_referrer_id", "referrer_id"),
    )


class Admin(Base):
    __tablename__ = "admins"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role: Mapped[e.AdminRole] = mapped_column(pg_enum(e.AdminRole))
    added_by: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(TS, server_default=NOW)


class PremiumPlan(Base):
    __tablename__ = "premium_plans"
    id: Mapped[int] = mapped_column(primary_key=True)
    months: Mapped[int] = mapped_column(sa.SmallInteger, unique=True)
    is_enabled: Mapped[bool] = mapped_column(default=True, server_default="true")
    provider_supported: Mapped[bool] = mapped_column(default=True, server_default="true")
    cost_ton: Mapped[Decimal | None] = mapped_column(TON)
    cost_updated_at: Mapped[datetime | None] = mapped_column(TS)
    markup_percent: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal(8), server_default="8")
    fixed_markup_usd: Mapped[Decimal] = mapped_column(USD, default=Decimal(0), server_default="0")
    fixed_price_usd: Mapped[Decimal | None] = mapped_column(USD)
    price_stars: Mapped[int | None] = mapped_column(Integer)
    reference_price_usd: Mapped[Decimal | None] = mapped_column(USD)
    badge: Mapped[str | None] = mapped_column(String(32))
    sort_order: Mapped[int] = mapped_column(sa.SmallInteger, default=0, server_default="0")
    __table_args__ = (sa.CheckConstraint("months IN (1,3,6,12)", name="ck_plan_months"),)


class StarPackage(Base):
    __tablename__ = "star_packages"
    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[int] = mapped_column(Integer, unique=True)
    is_enabled: Mapped[bool] = mapped_column(default=True, server_default="true")
    is_popular: Mapped[bool] = mapped_column(default=False, server_default="false")
    sort_order: Mapped[int] = mapped_column(sa.SmallInteger, default=0, server_default="0")
    __table_args__ = (sa.CheckConstraint("amount >= 50", name="ck_pkg_min"),)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(BigInteger, sa.Identity(), primary_key=True)
    public_id: Mapped[str] = mapped_column(String(16), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_type: Mapped[e.ProductType] = mapped_column(pg_enum(e.ProductType))
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("premium_plans.id"))
    plan_months: Mapped[int | None] = mapped_column(sa.SmallInteger)
    stars_amount: Mapped[int | None] = mapped_column(Integer)
    recipient_type: Mapped[e.RecipientType] = mapped_column(pg_enum(e.RecipientType))
    recipient_username: Mapped[str | None] = mapped_column(String(32))
    recipient_user_id: Mapped[int | None] = mapped_column(BigInteger)
    recipient_name: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[e.OrderStatus] = mapped_column(pg_enum(e.OrderStatus))
    payment_method: Mapped[e.PaymentMethod] = mapped_column(pg_enum(e.PaymentMethod))
    price_usd: Mapped[Decimal] = mapped_column(USD)
    discount_usd: Mapped[Decimal] = mapped_column(USD, default=Decimal(0), server_default="0")
    price_amount: Mapped[Decimal | None] = mapped_column(BIG)
    price_currency: Mapped[str | None] = mapped_column(String(8))
    cost_usd: Mapped[Decimal | None] = mapped_column(USD)
    cost_amount: Mapped[Decimal | None] = mapped_column(BIG)
    cost_currency: Mapped[str | None] = mapped_column(String(8))
    profit_usd: Mapped[Decimal | None] = mapped_column(USD)
    provider: Mapped[e.ProviderCode | None] = mapped_column(pg_enum(e.ProviderCode))
    provider_ref: Mapped[str | None] = mapped_column(String(128))
    idempotency_key: Mapped[str | None] = mapped_column(String(64))
    attempts: Mapped[int] = mapped_column(sa.SmallInteger, default=0, server_default="0")
    next_attempt_at: Mapped[datetime | None] = mapped_column(TS)
    locked_at: Mapped[datetime | None] = mapped_column(TS)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(String(500))
    bot_message_id: Mapped[int | None] = mapped_column(BigInteger)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(TS, server_default=NOW)
    paid_at: Mapped[datetime | None] = mapped_column(TS)
    completed_at: Mapped[datetime | None] = mapped_column(TS)
    updated_at: Mapped[datetime] = mapped_column(TS, server_default=NOW, onupdate=sa.func.now())
    __table_args__ = (
        sa.UniqueConstraint("user_id", "idempotency_key", name="uq_orders_idem"),
        sa.CheckConstraint("stars_amount IS NULL OR stars_amount >= 50", name="ck_orders_stars"),
        Index("ix_orders_user_created", "user_id", sa.text("created_at DESC")),
        Index(
            "ix_orders_queue",
            "status",
            "next_attempt_at",
            postgresql_where=text("status IN ('paid','processing','needs_review')"),
        ),
        Index(
            "ix_orders_completed_at",
            "completed_at",
            postgresql_where=text("status = 'completed'"),
        ),
        Index("ix_orders_created_at", "created_at"),
    )


class OrderEvent(Base):
    __tablename__ = "order_events"
    id: Mapped[int] = mapped_column(BigInteger, sa.Identity(), primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    from_status: Mapped[e.OrderStatus | None] = mapped_column(pg_enum(e.OrderStatus))
    to_status: Mapped[e.OrderStatus] = mapped_column(pg_enum(e.OrderStatus))
    actor: Mapped[str] = mapped_column(String(32))
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(TS, server_default=NOW)
    __table_args__ = (Index("ix_order_events_order", "order_id", "created_at"),)


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(BigInteger, sa.Identity(), primary_key=True)
    public_id: Mapped[str] = mapped_column(String(16), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"))
    purpose: Mapped[e.PaymentPurpose] = mapped_column(pg_enum(e.PaymentPurpose))
    method: Mapped[e.PaymentMethod] = mapped_column(pg_enum(e.PaymentMethod))
    status: Mapped[e.PaymentStatus] = mapped_column(pg_enum(e.PaymentStatus))
    amount: Mapped[Decimal] = mapped_column(BIG)
    received_amount: Mapped[Decimal | None] = mapped_column(BIG)
    currency: Mapped[str] = mapped_column(String(8))
    amount_usd: Mapped[Decimal] = mapped_column(USD)
    rate_used: Mapped[Decimal | None] = mapped_column(TON)
    ton_comment: Mapped[str | None] = mapped_column(String(32), unique=True)
    ton_tx_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    ton_sender: Mapped[str | None] = mapped_column(String(68))
    tg_charge_id: Mapped[str | None] = mapped_column(String(128), unique=True)
    is_late: Mapped[bool] = mapped_column(default=False, server_default="false")
    expires_at: Mapped[datetime | None] = mapped_column(TS)
    confirmed_at: Mapped[datetime | None] = mapped_column(TS)
    created_at: Mapped[datetime] = mapped_column(TS, server_default=NOW)
    raw: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}")
    __table_args__ = (
        sa.CheckConstraint("amount > 0", name="ck_payments_amount"),
        Index(
            "ix_payments_pending",
            "status",
            "expires_at",
            postgresql_where=text("status = 'pending'"),
        ),
        Index("ix_payments_user_created", "user_id", sa.text("created_at DESC")),
        Index("ix_payments_confirmed_at", "confirmed_at"),
    )


class BalanceTransaction(Base):
    __tablename__ = "balance_transactions"
    id: Mapped[int] = mapped_column(BigInteger, sa.Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount_usd: Mapped[Decimal] = mapped_column(USD)
    balance_after: Mapped[Decimal] = mapped_column(USD)
    type: Mapped[e.BalanceTxType] = mapped_column(pg_enum(e.BalanceTxType))
    ref_type: Mapped[str | None] = mapped_column(String(32))
    ref_id: Mapped[int | None] = mapped_column(BigInteger)
    comment: Mapped[str | None] = mapped_column(String(255))
    created_by: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(TS, server_default=NOW)
    __table_args__ = (Index("ix_baltx_user_created", "user_id", sa.text("created_at DESC")),)


class HotWalletTransaction(Base):
    __tablename__ = "hot_wallet_transactions"
    id: Mapped[int] = mapped_column(BigInteger, sa.Identity(), primary_key=True)
    direction: Mapped[e.Direction] = mapped_column(pg_enum(e.Direction))
    kind: Mapped[e.HotWalletTxKind] = mapped_column(pg_enum(e.HotWalletTxKind))
    amount_ton: Mapped[Decimal] = mapped_column(TON)
    fee_ton: Mapped[Decimal] = mapped_column(TON, default=Decimal(0), server_default="0")
    amount_usd: Mapped[Decimal | None] = mapped_column(USD)
    rate_used: Mapped[Decimal | None] = mapped_column(TON)
    tx_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    counterparty: Mapped[str | None] = mapped_column(String(68))
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"))
    payment_id: Mapped[int | None] = mapped_column(ForeignKey("payments.id"))
    created_by: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(TS, server_default=NOW)


class StarsTransaction(Base):
    __tablename__ = "stars_transactions"
    id: Mapped[int] = mapped_column(BigInteger, sa.Identity(), primary_key=True)
    direction: Mapped[e.Direction] = mapped_column(pg_enum(e.Direction))
    kind: Mapped[e.StarsTxKind] = mapped_column(pg_enum(e.StarsTxKind))
    amount: Mapped[int] = mapped_column(Integer)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"))
    payment_id: Mapped[int | None] = mapped_column(ForeignKey("payments.id"))
    tg_charge_id: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(TS, server_default=NOW)


class UnmatchedTonTx(Base):
    __tablename__ = "unmatched_ton_txs"
    id: Mapped[int] = mapped_column(BigInteger, sa.Identity(), primary_key=True)
    tx_hash: Mapped[str] = mapped_column(String(64), unique=True)
    amount_ton: Mapped[Decimal] = mapped_column(TON)
    comment: Mapped[str | None] = mapped_column(String(255))
    sender: Mapped[str | None] = mapped_column(String(68))
    resolution: Mapped[str] = mapped_column(String(64), default="pending", server_default="pending")
    resolved_by: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(TS, server_default=NOW)


class PromoCode(Base):
    __tablename__ = "promo_codes"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32))
    type: Mapped[e.PromoType] = mapped_column(pg_enum(e.PromoType))
    value: Mapped[Decimal] = mapped_column(USD)
    applies_to: Mapped[e.ProductScope] = mapped_column(pg_enum(e.ProductScope), default=e.ProductScope.ALL)
    min_order_usd: Mapped[Decimal | None] = mapped_column(USD)
    max_uses: Mapped[int | None] = mapped_column(Integer)
    used_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    per_user_limit: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    valid_from: Mapped[datetime | None] = mapped_column(TS)
    valid_to: Mapped[datetime | None] = mapped_column(TS)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
    __table_args__ = (Index("uq_promo_code_upper", sa.func.upper(sa.column("code")), unique=True),)


class PromoRedemption(Base):
    __tablename__ = "promo_redemptions"
    id: Mapped[int] = mapped_column(BigInteger, sa.Identity(), primary_key=True)
    promo_id: Mapped[int] = mapped_column(ForeignKey("promo_codes.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    discount_usd: Mapped[Decimal] = mapped_column(USD)
    __table_args__ = (sa.UniqueConstraint("promo_id", "order_id", name="uq_promo_order"),)


class ReferralReward(Base):
    __tablename__ = "referral_rewards"
    id: Mapped[int] = mapped_column(BigInteger, sa.Identity(), primary_key=True)
    referrer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    referred_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    amount_usd: Mapped[Decimal] = mapped_column(USD)
    status: Mapped[e.RewardStatus] = mapped_column(pg_enum(e.RewardStatus))
    created_at: Mapped[datetime] = mapped_column(TS, server_default=NOW)


class Expense(Base):
    __tablename__ = "expenses"
    id: Mapped[int] = mapped_column(BigInteger, sa.Identity(), primary_key=True)
    category: Mapped[e.ExpenseCategory] = mapped_column(pg_enum(e.ExpenseCategory))
    amount_usd: Mapped[Decimal] = mapped_column(USD)
    note: Mapped[str | None] = mapped_column(String(255))
    spent_on: Mapped[date] = mapped_column(sa.Date)
    created_by: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(TS, server_default=NOW)


class Broadcast(Base):
    __tablename__ = "broadcasts"
    id: Mapped[int] = mapped_column(BigInteger, sa.Identity(), primary_key=True)
    created_by: Mapped[int] = mapped_column(BigInteger)
    content: Mapped[dict[str, Any]] = mapped_column(JSONB)
    segment: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}")
    status: Mapped[e.BroadcastStatus] = mapped_column(pg_enum(e.BroadcastStatus))
    scheduled_at: Mapped[datetime | None] = mapped_column(TS)
    total: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    sent: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    failed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    cursor_user_id: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(TS, server_default=NOW)


class Channel(Base):
    __tablename__ = "channels"
    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    title: Mapped[str] = mapped_column(String(128))
    invite_link: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[Any] = mapped_column(JSONB)
    is_secret: Mapped[bool] = mapped_column(default=False, server_default="false")
    updated_by: Mapped[int | None] = mapped_column(BigInteger)
    updated_at: Mapped[datetime] = mapped_column(TS, server_default=NOW)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(BigInteger, sa.Identity(), primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(BigInteger)
    action: Mapped[str] = mapped_column(String(64))
    entity: Mapped[str | None] = mapped_column(String(64))
    entity_id: Mapped[str | None] = mapped_column(String(64))
    before: Mapped[Any] = mapped_column(JSONB, nullable=True)
    after: Mapped[Any] = mapped_column(JSONB, nullable=True)
    source: Mapped[str] = mapped_column(String(16), default="bot", server_default="bot")
    created_at: Mapped[datetime] = mapped_column(TS, server_default=NOW)
    __table_args__ = (Index("ix_audit_created", sa.text("created_at DESC")),)


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    id: Mapped[int] = mapped_column(BigInteger, sa.Identity(), primary_key=True)
    pair: Mapped[str] = mapped_column(String(16))
    rate: Mapped[Decimal] = mapped_column(Numeric(20, 9))
    source: Mapped[str] = mapped_column(String(32))
    fetched_at: Mapped[datetime] = mapped_column(TS, server_default=NOW)
    __table_args__ = (Index("ix_rates_pair_time", "pair", sa.text("fetched_at DESC")),)


class UserDailyActivity(Base):
    __tablename__ = "user_daily_activity"
    day: Mapped[date] = mapped_column(sa.Date, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)


class DailyStats(Base):
    __tablename__ = "daily_stats"
    day: Mapped[date] = mapped_column(sa.Date, primary_key=True)
    new_users: Mapped[int] = mapped_column(Integer, default=0)
    active_users: Mapped[int] = mapped_column(Integer, default=0)
    paying_users: Mapped[int] = mapped_column(Integer, default=0)
    orders_created: Mapped[int] = mapped_column(Integer, default=0)
    orders_completed: Mapped[int] = mapped_column(Integer, default=0)
    orders_failed: Mapped[int] = mapped_column(Integer, default=0)
    orders_refunded: Mapped[int] = mapped_column(Integer, default=0)
    premium_3m: Mapped[int] = mapped_column(Integer, default=0)
    premium_6m: Mapped[int] = mapped_column(Integer, default=0)
    premium_12m: Mapped[int] = mapped_column(Integer, default=0)
    stars_orders: Mapped[int] = mapped_column(Integer, default=0)
    stars_sold: Mapped[int] = mapped_column(Integer, default=0)
    cash_in_usd: Mapped[Decimal] = mapped_column(USD, default=Decimal(0))
    revenue_usd: Mapped[Decimal] = mapped_column(USD, default=Decimal(0))
    cost_usd: Mapped[Decimal] = mapped_column(USD, default=Decimal(0))
    gross_profit_usd: Mapped[Decimal] = mapped_column(USD, default=Decimal(0))
    expenses_usd: Mapped[Decimal] = mapped_column(USD, default=Decimal(0))
    referral_usd: Mapped[Decimal] = mapped_column(USD, default=Decimal(0))
    net_profit_usd: Mapped[Decimal] = mapped_column(USD, default=Decimal(0))
    revenue_by_method: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    avg_delivery_seconds: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    updated_at: Mapped[datetime] = mapped_column(TS, server_default=NOW)
