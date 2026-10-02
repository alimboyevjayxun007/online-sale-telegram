from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

import httpx

from app.core.config import get_settings
from app.core.money import from_nano


@dataclass
class IncomingTx:
    hash: str
    lt: int
    amount_ton: Decimal
    comment: str | None
    sender: str | None
    success: bool = True


class TonChainClient(Protocol):
    async def get_incoming(self, address: str, after_lt: int = 0) -> list[IncomingTx]: ...

    async def get_balance(self, address: str) -> Decimal: ...


class TonApiChain:
    """Read-only chain access through TonAPI (https://tonapi.io)."""

    def __init__(self) -> None:
        s = get_settings()
        self.base = "https://testnet.tonapi.io" if s.ton_network == "testnet" else "https://tonapi.io"
        key = s.tonapi_key.get_secret_value()
        self.headers = {"Authorization": f"Bearer {key}"} if key else {}

    async def get_incoming(self, address: str, after_lt: int = 0) -> list[IncomingTx]:
        params: dict[str, str | int] = {"limit": 100, "sort_order": "asc"}
        if after_lt:
            params["after_lt"] = after_lt
        async with httpx.AsyncClient(timeout=15, headers=self.headers) as c:
            r = await c.get(f"{self.base}/v2/blockchain/accounts/{address}/transactions", params=params)
            r.raise_for_status()
        out: list[IncomingTx] = []
        for tx in r.json().get("transactions", []):
            msg = tx.get("in_msg") or {}
            value = int(msg.get("value") or 0)
            if value <= 0 or msg.get("msg_type") != "int_msg":
                continue
            body = msg.get("decoded_body") or {}
            comment = body.get("text") if msg.get("decoded_op_name") == "text_comment" else None
            src = (msg.get("source") or {}).get("address")
            out.append(
                IncomingTx(tx["hash"], int(tx["lt"]), from_nano(value), comment, src, bool(tx.get("success", True)))
            )
        return out

    async def get_balance(self, address: str) -> Decimal:
        async with httpx.AsyncClient(timeout=15, headers=self.headers) as c:
            r = await c.get(f"{self.base}/v2/accounts/{address}")
            r.raise_for_status()
        return from_nano(int(r.json()["balance"]))
