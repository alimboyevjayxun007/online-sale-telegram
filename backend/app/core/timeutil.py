from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.core.config import get_settings


def tz() -> ZoneInfo:
    return ZoneInfo(get_settings().timezone)


def now_utc() -> datetime:
    return datetime.now(UTC)


def today_local() -> date:
    return datetime.now(tz()).date()


def day_bounds_utc(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=tz())
    return start.astimezone(UTC), (start + timedelta(days=1)).astimezone(UTC)


def local_to_utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=tz()).astimezone(UTC)
