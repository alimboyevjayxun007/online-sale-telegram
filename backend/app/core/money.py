from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

NANO = Decimal(10) ** 9


def D(value: object) -> Decimal:
    """Build a Decimal from str/int/Decimal; floats are rejected on purpose."""
    if isinstance(value, float):
        raise TypeError("float is not allowed for money")
    return Decimal(str(value))


def quantize(value: Decimal, step: str = "0.000001") -> Decimal:
    return value.quantize(Decimal(step), rounding=ROUND_HALF_UP)


def round_up(value: Decimal, step: Decimal) -> Decimal:
    """Round up to a multiple of ``step`` (e.g. 0.05)."""
    if step <= 0:
        return value
    return (value / step).to_integral_value(rounding=ROUND_CEILING) * step


def ceil_places(value: Decimal, places: int = 2) -> Decimal:
    return round_up(value, Decimal(1).scaleb(-places))


def to_nano(ton: Decimal) -> int:
    return int((ton * NANO).to_integral_value(rounding=ROUND_HALF_UP))


def from_nano(nano: int) -> Decimal:
    return Decimal(nano) / NANO


def round_to(value: Decimal, base: int) -> int:
    """Round to nearest multiple of ``base`` (e.g. 1000 so'm)."""
    return int((value / base).to_integral_value(rounding=ROUND_HALF_UP)) * base
