import hashlib
import hmac
import json
import time
from typing import Any
from urllib.parse import parse_qsl

from cryptography.fernet import Fernet

from app.core.errors import ExpiredInitData, InvalidInitData


def validate_init_data(init_data: str, bot_token: str, max_age: int = 86_400) -> dict[str, str]:
    """Validate Telegram Mini App initData (official HMAC algorithm)."""
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=True))
    except ValueError as exc:
        raise InvalidInitData() from exc
    received_hash = pairs.pop("hash", None)
    if not received_hash or not bot_token:
        raise InvalidInitData()
    check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calc = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc, received_hash):
        raise InvalidInitData()
    try:
        auth_date = int(pairs["auth_date"])
    except (KeyError, ValueError) as exc:
        raise InvalidInitData() from exc
    if time.time() - auth_date > max_age:
        raise ExpiredInitData()
    return pairs


def parse_init_user(pairs: dict[str, str]) -> dict[str, Any]:
    try:
        user = json.loads(pairs["user"])
        int(user["id"])
    except (KeyError, ValueError, TypeError) as exc:
        raise InvalidInitData() from exc
    return dict(user)


def build_init_data(user: dict[str, object], bot_token: str, auth_date: int | None = None) -> str:
    """Create a signed initData string (used by tests and the dev mock)."""
    from urllib.parse import urlencode

    pairs = {"user": json.dumps(user, separators=(",", ":")), "auth_date": str(auth_date or int(time.time()))}
    check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    pairs["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(pairs)


def fernet(key: str) -> Fernet:
    return Fernet(key.encode())


def encrypt(value: str, key: str) -> str:
    return fernet(key).encrypt(value.encode()).decode()


def decrypt(token: str, key: str) -> str:
    return fernet(key).decrypt(token.encode()).decode()
