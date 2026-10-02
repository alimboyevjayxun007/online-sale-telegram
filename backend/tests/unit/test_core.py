import time

import pytest

from app.core.errors import ExpiredInitData, InvalidInitData
from app.core.money import D, ceil_places, round_up, to_nano
from app.core.security import build_init_data, decrypt, encrypt, validate_init_data
from decimal import Decimal

TOKEN = "123456:TESTTOKENTESTTOKENTESTTOKENTESTTOKEN"


def test_init_data_valid_tampered_expired():
    raw = build_init_data({"id": 7, "first_name": "A"}, TOKEN)
    assert validate_init_data(raw, TOKEN)["auth_date"]
    with pytest.raises(InvalidInitData):
        validate_init_data(raw.replace("first_name", "first_nam3"), TOKEN)
    with pytest.raises(InvalidInitData):
        validate_init_data(raw, "999:OTHER")
    old = build_init_data({"id": 7}, TOKEN, auth_date=int(time.time()) - 100_000)
    with pytest.raises(ExpiredInitData):
        validate_init_data(old, TOKEN)
    with pytest.raises(InvalidInitData):
        validate_init_data("garbage", TOKEN)


def test_money():
    assert round_up(Decimal("13.11"), Decimal("0.05")) == Decimal("13.15")
    assert round_up(Decimal("13.15"), Decimal("0.05")) == Decimal("13.15")
    assert ceil_places(Decimal("4.381")) == Decimal("4.39")
    assert to_nano(Decimal("10.5")) == 10_500_000_000
    with pytest.raises(TypeError):
        D(1.5)


def test_fernet_roundtrip():
    key = "yQ0m3m1h0m8V8p5m6F3K8e6k1Zf2o9fX3m5v7b9c1d4="
    assert decrypt(encrypt("cookie", key), key) == "cookie"
