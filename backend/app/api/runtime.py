"""Process-wide wiring of external collaborators (bot messenger, stars gateway, providers, TON clients).

Everything is created lazily and can be replaced in tests via ``set_runtime``.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.enums import ProviderCode
from app.core.redis import get_redis
from app.providers.fulfillment.base import FulfillmentProvider
from app.providers.fulfillment.bot_stars import BotStarsProvider
from app.providers.fulfillment.fragment import FragmentApiProvider, FragmentDirectProvider, FragmentWebClient
from app.providers.fulfillment.gateway import StarsGateway
from app.providers.fulfillment.mock import MockProvider
from app.providers.ton.chain import TonApiChain, TonChainClient
from app.providers.ton.wallet import TonSigner, TonUtilsSigner
from app.services.checkout_service import CheckoutService
from app.services.fulfillment_service import FulfillmentService
from app.services.hot_wallet_service import HotWalletService
from app.services.notification_service import Messenger, NotificationService, NullMessenger
from app.services.pricing_service import PricingService
from app.services.promo_service import PromoService
from app.services.rate_service import RateService
from app.services.settings_service import SettingsService


@dataclass
class Runtime:
    messenger: Messenger = field(default_factory=NullMessenger)
    stars: StarsGateway | None = None
    chain: TonChainClient | None = None
    signer: TonSigner | None = None
    mock: MockProvider | None = None  # only set in development/tests
    bot: Any = None
    _signer_tried: bool = False

    def get_chain(self) -> TonChainClient:
        if self.chain is None:
            self.chain = TonApiChain()
        return self.chain

    def get_signer(self) -> TonSigner | None:
        if self.signer is None and not self._signer_tried:
            self._signer_tried = True
            path = get_settings().hot_wallet_mnemonic_file
            if path and Path(path).exists():
                self.signer = TonUtilsSigner()
        return self.signer


_runtime = Runtime()


def runtime() -> Runtime:
    return _runtime


def set_runtime(rt: Runtime) -> None:
    global _runtime
    _runtime = rt


async def build_fragment_client(settings: SettingsService, signer: TonSigner | None) -> FragmentWebClient | None:
    raw = await settings.get("fragment.cookies")
    if not raw or signer is None:
        return None
    cookies = dict(p.strip().split("=", 1) for p in str(raw).split(";") if "=" in p)
    return FragmentWebClient(cookies, {"address": signer.address, "chain": "-239"})


async def build_providers(settings: SettingsService, rt: Runtime) -> dict[ProviderCode, FulfillmentProvider]:
    providers: dict[ProviderCode, FulfillmentProvider] = {}
    signer = rt.get_signer()
    providers[ProviderCode.FRAGMENT_DIRECT] = FragmentDirectProvider(
        await build_fragment_client(settings, signer), signer
    )
    providers[ProviderCode.FRAGMENT_API] = FragmentApiProvider()
    if rt.stars is not None:
        providers[ProviderCode.BOT_STARS] = BotStarsProvider(rt.stars)
    if rt.mock is not None:
        providers[ProviderCode.MOCK] = rt.mock
    return providers


class Services:
    """Per-request/per-job service container bound to one DB session."""

    def __init__(self, session: AsyncSession, rt: Runtime | None = None) -> None:
        self.session = session
        self.rt = rt or runtime()
        self.settings = SettingsService(session)
        self.rates = RateService(session, get_redis())
        self.notifier = NotificationService(self.rt.messenger, self.settings)
        self.pricing = PricingService(self.rates, self.settings, PromoService(session))
        self.checkout = CheckoutService(session, self.settings, self.pricing, self.notifier)

    async def fulfillment(self) -> FulfillmentService:
        providers = await build_providers(self.settings, self.rt)
        return FulfillmentService(self.session, self.settings, self.rates, providers, self.notifier, self.rt.stars)

    def hot_wallet(self) -> HotWalletService:
        return HotWalletService(self.session, self.settings, self.rt.get_chain(), self.rt.get_signer(), self.rates)


async def resolve_recipient(
    svc: "Services", username: str, product: str = "premium", months: int = 3
) -> dict[str, Any]:
    """Look the recipient up through the first live provider; if none is reachable accept the username unverified."""
    providers = await build_providers(svc.settings, svc.rt)
    for code in (ProviderCode.FRAGMENT_DIRECT, ProviderCode.MOCK):
        p = providers.get(code)
        if p is not None and await p.is_available():
            info = await p.resolve_recipient(username, product, months)
            return {"found": info.found, "name": info.name, "photo_url": info.photo_url,
                    "can_receive": info.can_receive, "reason": info.reason, "username": username}  # fmt: skip
    return {"found": True, "name": None, "photo_url": None, "can_receive": True, "reason": None,
            "username": username, "verified": False}  # fmt: skip
