"""Hot wallet signer (tonutils). The mnemonic is read from an encrypted file, never from logs/env."""

from pathlib import Path
from typing import Protocol

from ton_core import Address, Cell, NetworkGlobalID
from tonutils.clients.http import TonapiClient
from tonutils.contracts.wallet import WalletV4R2, WalletV5R1

from app.core.config import get_settings
from app.core.security import decrypt, encrypt


class TonSigner(Protocol):
    address: str

    async def send(self, to: str, amount_nano: int, comment: str | None = None, body_b64: str | None = None) -> str: ...


def _wallet_cls(version: str):  # type: ignore[no-untyped-def]
    return WalletV4R2 if version.lower() in ("v4r2", "v4") else WalletV5R1


def _client() -> TonapiClient:
    s = get_settings()
    net = NetworkGlobalID.TESTNET if s.ton_network == "testnet" else NetworkGlobalID.MAINNET
    return TonapiClient(net, api_key=s.tonapi_key.get_secret_value() or None)


def generate_wallet_file(path: str | None = None) -> tuple[str, list[str]]:
    """Create a brand-new wallet, store the Fernet-encrypted mnemonic and return (address, mnemonic)."""
    s = get_settings()
    wallet, _, _, mnemonic = _wallet_cls(s.hot_wallet_version).create(_client())
    target = Path(path or s.hot_wallet_mnemonic_file)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(encrypt(" ".join(mnemonic), s.encryption_key.get_secret_value()))
    target.chmod(0o600)
    return wallet.address.to_str(is_bounceable=False), mnemonic


class TonUtilsSigner:
    def __init__(self) -> None:
        s = get_settings()
        raw = decrypt(Path(s.hot_wallet_mnemonic_file).read_text(), s.encryption_key.get_secret_value())
        self.client = _client()
        self.wallet, *_ = _wallet_cls(s.hot_wallet_version).from_mnemonic(self.client, raw)
        self.address = self.wallet.address.to_str(is_bounceable=False)

    async def send(self, to: str, amount_nano: int, comment: str | None = None, body_b64: str | None = None) -> str:
        await self.client.connect()
        try:
            body: Cell | str | None = Cell.one_from_boc(body_b64) if body_b64 else comment
            msg = await self.wallet.transfer(Address(to), amount_nano, body=body, bounce=False)
            return str(msg.normalized_hash)
        finally:
            await self.client.close()
