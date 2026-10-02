import pytest
from sqlalchemy import select

from app.api.runtime import Runtime, Services, set_runtime
from app.bot.gateway import AiogramMessenger, AiogramStarsGateway
from app.bot.setup import create_dispatcher
from app.core.db import session_maker
from app.core.enums import OrderStatus
from app.models import Order, User
from app.providers.fulfillment.mock import MockProvider
from tests.fake_telegram import Client, make_bot
from tests.helpers import fund, seed


@pytest.fixture
async def world(session):
    await seed(session)
    await session.commit()
    bot, tg = make_bot()
    rt = Runtime(bot=bot, messenger=AiogramMessenger(bot), stars=AiogramStarsGateway(bot), mock=MockProvider())
    set_runtime(rt)
    dp = create_dispatcher(rt)

    class W:
        pass

    w = W()
    w.bot, w.tg, w.rt, w.dp, w.session = bot, tg, rt, dp, session
    w.user = lambda uid, username=None, **kw: Client(dp, bot, uid, username or f"user{uid}", **kw)
    yield w
    set_runtime(Runtime())


async def deliver_pending(w):
    async with session_maker()() as s:
        svc = Services(s, w.rt)
        while await (await svc.fulfillment()).process_next():
            pass
        await s.commit()


def styles(tg):
    return {b.text: b.style for b in tg.buttons()}


async def test_start_language_then_menu_with_colored_buttons(world):
    u = world.user(1, "ali")
    await u.say("/start")
    assert "Tilni tanlang" in world.tg.last_text()
    assert [b.text for b in world.tg.buttons()] == ["🇺🇿 O'zbekcha", "🇷🇺 Русский", "🇬🇧 English"]
    await u.press_button(world.tg, "Русский")
    text, st = world.tg.last_text(), styles(world.tg)
    assert "Soft-tg-Market" in text and "Ваш баланс" in text
    assert st["💎 Купить Premium"] == "success" and st["⭐ Купить Stars"] == "success"
    assert all(b.style in (None, "primary", "success", "danger") for b in world.tg.buttons())
    assert not any("Админ" in b.text for b in world.tg.buttons())
    await u.say("/start")
    assert "Здравствуйте" in world.tg.last_text()  # language remembered, no second language prompt


async def test_referral_deep_link_binds_once(world, session):
    a, b = world.user(10, "refa"), world.user(11, "refb")
    await a.say("/start")
    await b.say("/start ref_10")
    await b.say("/start ref_999")
    session.expire_all()
    assert (await session.get(User, 11)).referrer_id == 10


async def test_buy_premium_with_balance_end_to_end(world, session):
    u = world.user(20, "buyer")
    await u.say("/start")
    await u.press_button(world.tg, "O'zbekcha")
    await fund(session, await session.get(User, 20), 100)
    await session.commit()
    await u.press_button(world.tg, "Premium sotib olish")
    assert "Kimga" in world.tg.last_text()
    await u.press_button(world.tg, "O'zimga")
    assert "Muddatni tanlang" in world.tg.last_text()
    labels = [b.text for b in world.tg.buttons()]
    assert any("12 oy · 31.50 $" in x for x in labels) and any("tez kunda" in x for x in labels)
    soon = [b for b in world.tg.buttons() if "tez kunda" in b.text][0]
    await u.press(soon.callback_data)
    assert world.tg.of("AnswerCallbackQuery")[-1].show_alert is True  # 1-month is not purchasable
    await u.press_button(world.tg, "12 oy")
    assert "31.50 $" in world.tg.last_text() and "403 000" in world.tg.last_text()
    pay_btn = [b for b in world.tg.buttons() if "Balansdan" in b.text]
    assert pay_btn and pay_btn[0].text.endswith("31.50 $")
    await u.press(pay_btn[0].callback_data)
    assert "To'lov qabul qilindi" in world.tg.last_text()
    session.expire_all()
    order = await session.scalar(select(Order))
    assert order.status == OrderStatus.PAID and order.bot_message_id
    price = order.price_usd
    await deliver_pending(world)
    assert any("Tayyor" in t and "12 oyga" in t for t in world.tg.texts())
    session.expire_all()
    assert (await session.get(User, 20)).balance_usd == 100 - price


async def test_buy_for_other_via_username_and_promo(world, session):
    from decimal import Decimal

    from app.core.enums import PromoType
    from app.models import PromoCode

    session.add(PromoCode(code="HELLO", type=PromoType.FIXED_USD, value=Decimal("1.5")))
    await session.commit()
    u = world.user(30, "gifter")
    await u.say("/start")
    await u.press_button(world.tg, "O'zbekcha")
    await fund(session, await session.get(User, 30), 50)
    await session.commit()
    await u.press_button(world.tg, "Premium")
    await u.press_button(world.tg, "Boshqa odamga")
    assert any("username" in t for t in world.tg.texts()[-3:])
    await u.say("a b")
    assert "noto'g'ri" in world.tg.last_text()
    await u.say("nouser_x")
    assert "topilmadi" in world.tg.last_text()
    await u.say("@Friend_One")
    assert "Friend_One" in world.tg.last_text() and "Mock" in world.tg.last_text()
    await u.press_button(world.tg, "davom etish")
    await u.press_button(world.tg, "3 oy")
    await u.press_button(world.tg, "Promokod")
    await u.say("hello")
    assert "−0.75 $" in world.tg.last_text() and "12.40 $" in world.tg.last_text()  # clamped by min margin
    await u.press_button(world.tg, "Balansdan")
    session.expire_all()
    order = await session.scalar(select(Order))
    assert (
        order.recipient_username == "Friend_One"
        and order.price_usd == Decimal("12.40")
        and order.discount_usd == Decimal("0.75")
    )
    await u.say("/start")
    await u.press_button(world.tg, "Buyurtmalarim")
    assert any(order.public_id in b.text for b in world.tg.buttons())


async def test_stars_invoice_precheckout_and_payment(world, session):
    u = world.user(40, "starpayer")
    await u.say("/start")
    await u.press_button(world.tg, "O'zbekcha")
    await u.press_button(world.tg, "Premium")
    await u.press_button(world.tg, "O'zimga")
    await u.press_button(world.tg, "3 oy")
    stars_btn = [b for b in world.tg.buttons() if "Stars" in b.text][0]
    assert "1 100" in stars_btn.text or "1100" in stars_btn.text
    await u.press(stars_btn.callback_data)
    inv = world.tg.of("SendInvoice")[-1]
    assert inv.currency == "XTR" and inv.prices[0].amount == 1100 and inv.payload.startswith("PM-")
    assert inv.reply_markup.inline_keyboard[0][0].pay is True
    await u.pre_checkout(inv.payload, 1100)
    assert world.tg.of("AnswerPreCheckoutQuery")[-1].ok is True
    await u.pre_checkout(inv.payload, 999)
    assert world.tg.of("AnswerPreCheckoutQuery")[-1].ok is False
    await u.paid(inv.payload, 1100, "chg-40")
    session.expire_all()
    order = await session.scalar(select(Order))
    assert order.status == OrderStatus.PAID
    await deliver_pending(world)
    assert any("Tayyor" in t for t in world.tg.texts())


async def test_ton_screen_has_copy_buttons_and_check(world, session):
    from app.services.settings_service import SettingsService

    await SettingsService(session).set("hot_wallet.address", "UQHotAddress")
    await session.commit()
    u = world.user(50, "tonpayer")
    await u.say("/start")
    await u.press_button(world.tg, "O'zbekcha")
    await u.press_button(world.tg, "Stars sotib")
    await u.press_button(world.tg, "O'zimga")
    await u.press_button(world.tg, "500")
    await u.press_button(world.tg, "TON")
    text = world.tg.last_text()
    assert "UQHotAddress" in text and "PM-" in text and "MAJBURIY" in text
    copies = [b for b in world.tg.buttons() if b.copy_text]
    assert len(copies) == 3 and copies[0].copy_text.text == "UQHotAddress"
    st = styles(world.tg)
    assert st["🔄 To'lovni tekshirish"] == "primary" and st["✖️ Buyurtmani bekor qilish"] == "danger"
    await u.press_button(world.tg, "bekor qilish")
    assert "bekor qilindi" in world.tg.last_text()
    session.expire_all()
    assert (await session.scalar(select(Order))).status == OrderStatus.CANCELLED


async def test_wallet_topup_flow(world, session):
    from app.services.settings_service import SettingsService

    await SettingsService(session).set("hot_wallet.address", "UQHotAddress")
    await session.commit()
    u = world.user(60, "topper")
    await u.say("/start")
    await u.press_button(world.tg, "O'zbekcha")
    await u.press_button(world.tg, "Hamyon")
    assert "Hamyon" in world.tg.last_text()
    await u.press_button(world.tg, "to'ldirish")
    await u.press_button(world.tg, "TON")
    await u.press_button(world.tg, "10 $")
    assert "TP-" in world.tg.last_text()


async def test_admin_panel_access_and_actions(world, session):
    owner, plain = world.user(1000, "owner"), world.user(70, "plain")
    await plain.say("/start")
    await plain.press_button(world.tg, "O'zbekcha")
    n = len(world.tg.calls)
    await plain.say("/admin")
    assert len(world.tg.calls) == n  # silently ignored for non-staff
    await plain.press("a:panel:open::0")
    assert not any("Admin panel" in t for t in world.tg.texts()[-2:])
    await owner.say("/start")
    await owner.press_button(world.tg, "O'zbekcha")
    assert any("Admin panel" in b.text for b in world.tg.buttons())
    await owner.say("/admin")
    assert "Admin panel" in world.tg.last_text() and "Bugun" in world.tg.last_text()
    await owner.press_button(world.tg, "Statistika")
    assert "MOLIYA" in world.tg.last_text() and "FOYDALANUVCHILAR" in world.tg.last_text()
    # ban flow through the confirmation screen
    await owner.say("/ban 70 spam")
    yes = [b for b in world.tg.buttons() if "tasdiqlash" in b.text][0]
    assert yes.style == "danger"
    await owner.press(yes.callback_data)
    assert "Bloklandi" in world.tg.last_text()
    n2 = len(world.tg.calls)
    await plain.say("/start")
    assert "bloklangan" in world.tg.last_text() and len(world.tg.calls) > n2
    await owner.say("/addbalance 70 12.5 sovg'a")
    assert "+12.50" in world.tg.last_text()
    yes = [b for b in world.tg.buttons() if "tasdiqlash" in b.text][0]
    await owner.press(yes.callback_data)
    assert "12.50" in world.tg.last_text()
    await owner.press(yes.callback_data)  # confirm tokens are single-use
    assert world.tg.of("AnswerCallbackQuery")[-1].show_alert is True


async def test_maintenance_blocks_users_not_admins(world, session):
    owner, u = world.user(1000, "owner"), world.user(80, "x")
    await owner.say("/start")
    await owner.say("/maintenance on")
    await u.say("/start")
    assert "texnik ishlar" in world.tg.last_text()
    await owner.say("/start")
    assert "Soft-tg-Market" in world.tg.last_text() or "Tilni" in world.tg.last_text()
    await owner.say("/maintenance off")
    await u.say("/start")
    assert "Soft-tg-Market" in world.tg.last_text()  # blocked newcomer still got registered; sees the menu


async def test_error_handler_replies_gracefully(world, session, monkeypatch):
    from app.bot.handlers import user as user_handlers

    async def boom(*a, **k):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(user_handlers, "screen_wallet", boom)
    u = world.user(90, "err")
    await u.say("/start")
    await u.press_button(world.tg, "O'zbekcha")
    await u.press_button(world.tg, "Hamyon")
    assert world.tg.of("AnswerCallbackQuery")[-1].show_alert is True
