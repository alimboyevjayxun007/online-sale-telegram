from enum import StrEnum


class ProductType(StrEnum):
    PREMIUM = "premium"
    STARS = "stars"


class RecipientType(StrEnum):
    SELF = "self"
    OTHER = "other"


class OrderStatus(StrEnum):
    AWAITING_PAYMENT = "awaiting_payment"
    PAID = "paid"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"
    REFUNDED = "refunded"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class PaymentPurpose(StrEnum):
    ORDER = "order"
    TOPUP = "topup"


class PaymentMethod(StrEnum):
    TON = "ton"
    STARS = "stars"
    BALANCE = "balance"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"
    FAILED = "failed"
    REFUNDED = "refunded"


class ProviderCode(StrEnum):
    FRAGMENT_DIRECT = "fragment_direct"
    FRAGMENT_API = "fragment_api"
    BOT_STARS = "bot_stars"
    MANUAL = "manual"
    MOCK = "mock"


class BalanceTxType(StrEnum):
    TOPUP = "topup"
    PURCHASE = "purchase"
    REFUND = "refund"
    REFERRAL_BONUS = "referral_bonus"
    REFERRAL_REVOKE = "referral_revoke"
    ADMIN_CREDIT = "admin_credit"
    ADMIN_DEBIT = "admin_debit"
    LATE_PAYMENT = "late_payment"
    OVERPAYMENT = "overpayment"
    UNDERPAYMENT = "underpayment"


class Direction(StrEnum):
    IN = "in"
    OUT = "out"


class HotWalletTxKind(StrEnum):
    USER_PAYMENT = "user_payment"
    FULFILLMENT = "fulfillment"
    WITHDRAWAL = "withdrawal"
    SWEEP = "sweep"
    NETWORK_FEE = "network_fee"
    MANUAL_DEPOSIT = "manual_deposit"
    REFUND_OUT = "refund_out"
    OTHER = "other"


class StarsTxKind(StrEnum):
    PAYMENT_IN = "payment_in"
    PREMIUM_GIFT = "premium_gift"
    REFUND = "refund"
    WITHDRAWAL_MANUAL = "withdrawal_manual"
    TELEGRAM_REFUND = "telegram_refund"


class AdminRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    SUPPORT = "support"


class PromoType(StrEnum):
    PERCENT = "percent"
    FIXED_USD = "fixed_usd"


class ProductScope(StrEnum):
    ALL = "all"
    PREMIUM = "premium"
    STARS = "stars"


class RewardStatus(StrEnum):
    CREDITED = "credited"
    REVOKED = "revoked"


class ExpenseCategory(StrEnum):
    SERVER = "server"
    DOMAIN = "domain"
    FRAGMENT_FEE = "fragment_fee"
    NETWORK_FEE = "network_fee"
    ADVERTISING = "advertising"
    SALARY = "salary"
    OTHER = "other"


class BroadcastStatus(StrEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
