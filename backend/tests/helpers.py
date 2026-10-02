from decimal import Decimal as Dc

from app.core.enums import ProviderCode
from app.core.redis import get_redis
from app.models import PremiumPlan, StarPackage, User
from app.providers.fulfillment.bot_stars import BotStarsProvider
from app.providers.fulfillment.mock import MockProvider
from app.services.checkout_service import CheckoutService
from app.services.fulfillment_service import FulfillmentService
from app.services.notification_service import NotificationService
from app.services.pricing_service import PricingService
from app.services.promo_service import PromoService
from app.services.rate_service import RateService
from app.services.settings_service import SettingsService


class FakeMessenger:
    def __init__(self):
        self.sent: list[tuple[int, str]] = []
        self.edits: list[tuple[int, int, str]] = []
        self._id = 100

    async def send(self, chat_id, text, reply_markup=None):
        self.sent.append((chat_id, text))
        self._id += 1
        return self._id

    async def edit(self, chat_id, message_id, text, reply_markup=None):
        self.edits.append((chat_id, message_id, text))
        return True

    async def send_content(self, chat_id, content):
        from app.services.notification_service import DeliveryBlocked, DeliveryRetry

        if chat_id in getattr(self, "blocked", set()):
            raise DeliveryBlocked()
        if getattr(self, "flood_once", False):
            self.flood_once = False
            raise DeliveryRetry(0.01)
        self.content_sent = getattr(self, "content_sent", []) + [(chat_id, content)]

    def texts(self, chat_id=None):
        return [t for c, t in self.sent if chat_id is None or c == chat_id] + [
            t for c, _, t in self.edits if chat_id is None or c == chat_id
        ]


class FakeStars:
    def __init__(self, balance=10_000):
        self.balance = balance
        self.gifts: list[tuple[int, int, int]] = []
        self.refunds: list[tuple[int, str]] = []
        self.fail_refund = False

    async def gift_premium(self, user_id, months, star_count):
        self.gifts.append((user_id, months, star_count))
        self.balance -= star_count

    async def star_balance(self):
        return self.balance

    async def refund_star_payment(self, user_id, charge_id):
        if self.fail_refund:
            raise RuntimeError("telegram said no")
        self.refunds.append((user_id, charge_id))

    async def create_invoice_link(self, title, description, payload, amount):
        return f"https://t.me/$inv_{payload}"

    async def send_invoice(self, chat_id, title, description, payload, amount):
        return 1


class Env:
    """Wires all services against one session with fake outside world."""

    def __init__(self, session, mode="ok"):
        self.session = session
        self.messenger = FakeMessenger()
        self.stars = FakeStars()
        self.mock = MockProvider(mode)
        self.settings = SettingsService(session)
        self.rates = RateService(session, get_redis())
        self.notifier = NotificationService(self.messenger, self.settings)
        self.pricing = PricingService(self.rates, self.settings, PromoService(session))
        self.checkout = CheckoutService(session, self.settings, self.pricing, self.notifier)
        self.providers = {ProviderCode.MOCK: self.mock}

    def fulfillment(self, providers=None):
        return FulfillmentService(
            self.session, self.settings, self.rates, providers or self.providers, self.notifier, self.stars
        )

    def with_bot_stars(self):
        self.providers = {ProviderCode.BOT_STARS: BotStarsProvider(self.stars), ProviderCode.MOCK: self.mock}
        return self


async def seed(session):
    rs = RateService(session, get_redis())
    await rs.set_rate("TON_USD", Dc(3), "t")
    await rs.set_rate("USD_UZS", Dc(12800), "t")
    for months, cost, stars in [(3, "4.00", 1100), (6, "5.33", 1650), (12, "9.66", 2750)]:
        session.add(PremiumPlan(months=months, cost_ton=Dc(cost), price_stars=stars, sort_order=months))
    session.add(PremiumPlan(months=1, is_enabled=False, provider_supported=False))
    for a in (50, 500):
        session.add(StarPackage(amount=a))
    await session.flush()


async def plan_id(session, months):
    from sqlalchemy import select

    return await session.scalar(select(PremiumPlan.id).where(PremiumPlan.months == months))


async def fund(session, user: User, amount):
    from app.core.enums import BalanceTxType
    from app.services.balance_service import BalanceService

    await BalanceService(session).credit(user.id, Dc(amount), BalanceTxType.ADMIN_CREDIT)
