class AppError(Exception):
    code = "ERROR"
    http_status = 400

    def __init__(self, message: str = "", **details: object) -> None:
        super().__init__(message or self.code)
        self.message = message or self.code
        self.details = details


class ValidationFailed(AppError):
    code, http_status = "VALIDATION_ERROR", 400


class InvalidInitData(AppError):
    code, http_status = "INIT_DATA_INVALID", 401


class ExpiredInitData(AppError):
    code, http_status = "INIT_DATA_EXPIRED", 401


class Forbidden(AppError):
    code, http_status = "FORBIDDEN", 403


class UserBanned(AppError):
    code, http_status = "USER_BANNED", 403


class NotFound(AppError):
    code, http_status = "NOT_FOUND", 404


class InvalidState(AppError):
    code, http_status = "INVALID_STATE", 409


class PriceChanged(AppError):
    code, http_status = "PRICE_CHANGED", 409


class Duplicate(AppError):
    code, http_status = "DUPLICATE", 409


class RecipientNotFound(AppError):
    code, http_status = "RECIPIENT_NOT_FOUND", 422


class RecipientCannotReceive(AppError):
    code, http_status = "RECIPIENT_CANNOT_RECEIVE", 422


class InsufficientBalance(AppError):
    code, http_status = "INSUFFICIENT_BALANCE", 422


class PromoInvalid(AppError):
    code, http_status = "PROMO_INVALID", 422


class MethodDisabled(AppError):
    code, http_status = "METHOD_DISABLED", 422


class PlanUnavailable(AppError):
    code, http_status = "PLAN_UNAVAILABLE", 422


class RateLimited(AppError):
    code, http_status = "RATE_LIMITED", 429


class Maintenance(AppError):
    code, http_status = "MAINTENANCE", 503


class ProviderUnavailable(AppError):
    """Temporary provider problem — safe to retry (money was NOT sent)."""

    code, http_status = "PROVIDER_UNAVAILABLE", 503


class RecipientInvalid(AppError):
    """Permanent failure — delivery impossible, refund."""

    code, http_status = "RECIPIENT_INVALID", 422


class ProviderUncertain(AppError):
    """Money may have been sent but the outcome is unknown — needs human review."""

    code, http_status = "PROVIDER_UNCERTAIN", 503
