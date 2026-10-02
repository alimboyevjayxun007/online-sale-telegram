from decimal import Decimal, InvalidOperation

import structlog
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    KeyboardButton,
    KeyboardButtonRequestUsers,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.runtime import Runtime, Services, resolve_recipient
from app.bot.callbacks import Adm, Fl, Menu, Ord, Pay, Set, Wal
from app.bot.helpers import dt, order_what, show, stars_fmt, toast, ton, usd, uzs, webapp_url, who_label
from app.bot.keyboards import btn, kb
from app.bot.states import Flow
from app.core.config import get_settings
from app.core.enums import OrderStatus, PaymentMethod, ProductType, RecipientType
from app.core.errors import AppError
from app.core.money import D
from app.i18n import t
from app.models import Order, PremiumPlan, PromoCode, User
from app.services.balance_service import BalanceService
from app.services.checkout_service import CheckoutResult, CreateOrderRequest, normalize_username
from app.services.order_service import OrderService
from app.services.pricing_service import Quote
from app.services.promo_service import PromoService
from app.services.referral_service import ReferralService

log = structlog.get_logger()
router = Router(name="user")
STATUS_ICON = {"awaiting_payment": "⏳", "paid": "💳", "processing": "⚙️", "completed": "✅", "failed": "❌",
               "needs_review": "🔍", "refunded": "↩️", "expired": "⌛️", "cancelled": "🚫"}  # fmt: skip
TOPUP_AMOUNTS = [5, 10, 25, 50, 100]


# ======================= menu =======================
async def menu_screen(ev: Message | CallbackQuery, user: User, lang: str, role: object, new: bool = False) -> None:
    text = t(lang, "welcome", name=user.first_name or "", balance=usd(user.balance_usd))
    app_btn = (
        btn(t(lang, "b_app"), web_app=webapp_url("/"), style="primary")
        if get_settings().webapp_url.startswith("https://")
        else None
    )
    markup = kb(
        app_btn,
        btn(t(lang, "b_premium"), Menu(a="premium"), style="success"),
        btn(t(lang, "b_stars"), Menu(a="stars"), style="success"),
        [
            btn(t(lang, "b_wallet", balance=usd(user.balance_usd)), Menu(a="wallet")),
            btn(t(lang, "b_orders"), Menu(a="orders")),
        ],
        [btn(t(lang, "b_ref"), Menu(a="ref")), btn(t(lang, "b_settings"), Menu(a="settings"))],
        btn(t(lang, "b_help"), Menu(a="help")),
        btn(t(lang, "b_admin"), Adm(sec="panel"), style="primary") if role else None,
    )
    await show(ev, text, markup, new=new)


def lang_keyboard(prefix_back: bool = False, lang: str = "uz") -> InlineKeyboardMarkup:
    return kb(
        [
            btn("🇺🇿 O'zbekcha", Set(a="setlang", v="uz"), style="primary"),
            btn("🇷🇺 Русский", Set(a="setlang", v="ru")),
            btn("🇬🇧 English", Set(a="setlang", v="en")),
        ],
        btn(t(lang, "b_back"), Menu(a="settings")) if prefix_back else None,
    )


@router.message(CommandStart())
async def cmd_start(
    m: Message, state: FSMContext, user: User, lang: str, created: bool, role: object, svc: Services
) -> None:
    await state.clear()
    arg = (m.text or "").split(maxsplit=1)[1].strip() if m.text and " " in m.text else ""
    if created:
        await m.answer(t(lang, "choose_lang"), reply_markup=lang_keyboard())
        return
    await menu_screen(m, user, lang, role, new=True)
    if arg in ("premium", "stars", "wallet", "orders", "ref"):
        await dispatch_menu(arg, m, state, user, lang, svc)
    elif arg.startswith("order_"):
        await order_view(m, svc, user, lang, arg[6:])


@router.message(Command("cancel"))
@router.message(F.text.in_({"✖️ Bekor qilish", "✖️ Отмена", "✖️ Cancel"}))
async def cmd_cancel(m: Message, state: FSMContext, user: User, lang: str, role: object) -> None:
    await state.clear()
    tmp = await m.answer(t(lang, "cancelled"), reply_markup=ReplyKeyboardRemove())
    await tmp.delete()
    await menu_screen(m, user, lang, role, new=True)


@router.message(Command("app"))
async def cmd_app(m: Message, lang: str) -> None:
    if get_settings().webapp_url.startswith("https://"):
        await m.answer(
            t(lang, "b_app"), reply_markup=kb(btn(t(lang, "b_app"), web_app=webapp_url("/"), style="primary"))
        )


@router.message(Command("help"))
async def cmd_help(m: Message, svc: Services, lang: str) -> None:
    await help_screen(m, svc, lang)


@router.message(Command("premium"))
async def cmd_premium(m: Message, state: FSMContext, user: User, lang: str, svc: Services) -> None:
    await dispatch_menu("premium", m, state, user, lang, svc)


@router.message(Command("stars"))
async def cmd_stars(m: Message, state: FSMContext, user: User, lang: str, svc: Services) -> None:
    await dispatch_menu("stars", m, state, user, lang, svc)


@router.message(Command("wallet"))
async def cmd_wallet(m: Message, state: FSMContext, user: User, lang: str, svc: Services) -> None:
    await dispatch_menu("wallet", m, state, user, lang, svc)


@router.message(Command("orders"))
async def cmd_orders(m: Message, state: FSMContext, user: User, lang: str, svc: Services) -> None:
    await dispatch_menu("orders", m, state, user, lang, svc)


@router.message(Command("referral"))
async def cmd_ref(m: Message, state: FSMContext, user: User, lang: str, svc: Services) -> None:
    await dispatch_menu("ref", m, state, user, lang, svc)


@router.message(Command("lang"))
async def cmd_lang(m: Message, lang: str) -> None:
    await m.answer(t(lang, "choose_lang"), reply_markup=lang_keyboard())


async def dispatch_menu(
    action: str, ev: Message | CallbackQuery, state: FSMContext, user: User, lang: str, svc: Services
) -> None:
    await state.clear()
    if action == "premium":
        await state.update_data(flow={"product": "premium"})
        await screen_who(ev, state, user, lang)
    elif action == "stars":
        await state.update_data(flow={"product": "stars"})
        await screen_who(ev, state, user, lang)
    elif action == "wallet":
        await screen_wallet(ev, svc, user, lang)
    elif action == "orders":
        await screen_orders(ev, svc, user, lang, 0)
    elif action == "ref":
        await screen_referral(ev, svc, user, lang)
    elif action == "settings":
        await screen_settings(ev, user, lang)
    elif action == "help":
        await help_screen(ev, svc, lang)


@router.callback_query(Menu.filter())
async def on_menu(
    cb: CallbackQuery, callback_data: Menu, state: FSMContext, user: User, lang: str, role: object, svc: Services
) -> None:
    await toast(cb)
    a = callback_data.a
    if a == "home" or a == "subcheck":
        await state.clear()
        await menu_screen(cb, user, lang, role)
    else:
        await dispatch_menu(a, cb, state, user, lang, svc)


@router.callback_query(Set.filter())
async def on_set(cb: CallbackQuery, callback_data: Set, user: User, lang: str, role: object, svc: Services) -> None:
    if callback_data.a == "lang":
        await toast(cb)
        await show(cb, t(lang, "choose_lang"), lang_keyboard(True, lang))
    elif callback_data.a == "setlang":
        if callback_data.v in ("uz", "ru", "en"):
            user.language = callback_data.v
            lang = callback_data.v
        await toast(cb)
        await menu_screen(cb, user, lang, role)
    elif callback_data.a == "mkt":
        user.marketing_opt_out = not user.marketing_opt_out
        await toast(cb)
        await screen_settings(cb, user, lang)


# ======================= purchase flow =======================
def _flow(data: dict) -> dict:  # type: ignore[type-arg]
    return dict(data.get("flow") or {})


async def screen_who(ev: Message | CallbackQuery, state: FSMContext, user: User, lang: str) -> None:
    flow = _flow(await state.get_data())
    prod = t(lang, "b_premium") if flow.get("product") == "premium" else t(lang, "b_stars")
    text = t(lang, "who_title", prod=prod) + "\n\n" + t(lang, "who_ask")
    self_btn = btn(
        t(lang, "b_self", u=user.username) if user.username else t(lang, "b_self_nouser"),
        Fl(s="who", v="self"),
        style="primary",
    )
    note = ""
    if not user.username and flow.get("product") == "premium":
        note = "\n\n" + t(lang, "no_username_note")
    await show(
        ev,
        text + note,
        kb([self_btn, btn(t(lang, "b_other"), Fl(s="who", v="other"))], btn(t(lang, "b_back"), Menu(a="home"))),
    )


async def screen_plans(ev: Message | CallbackQuery, svc: Services, state: FSMContext, user: User, lang: str) -> None:
    from app.services.catalog_service import CatalogService

    flow = _flow(await state.get_data())
    plans = await CatalogService(svc.session, svc.settings, svc.pricing, svc.rates).plans()
    rows = []
    for p in plans:
        if p["coming_soon"]:
            rows.append(btn(t(lang, "plan_soon"), Fl(s="soon")))
        elif p["available"]:
            badge = f"{p['badge']} " if p.get("badge") else ""
            rows.append(
                btn(
                    t(lang, "plan_btn", badge=badge, months=p["months"], price=usd(p["price_usd"])),
                    Fl(s="plan", v=str(p["id"])),
                    style="primary" if p.get("badge") else None,
                )
            )
    text = t(lang, "months_title", who=who_label(lang, flow, user)) + "\n\n" + t(lang, "months_note")
    await show(
        ev,
        text,
        kb(*rows, [btn(t(lang, "b_back"), Fl(s="back_who")), btn(t(lang, "b_cancel"), Menu(a="home"), style="danger")]),
    )


async def screen_packages(ev: Message | CallbackQuery, svc: Services, state: FSMContext, user: User, lang: str) -> None:
    from app.services.catalog_service import CatalogService

    flow = _flow(await state.get_data())
    pkgs = await CatalogService(svc.session, svc.settings, svc.pricing, svc.rates).star_packages()
    buttons = [
        btn(
            ("🔥 " if p["popular"] else "") + f"⭐ {p['amount']} · {usd(p['price_usd'])}",
            Fl(s="pkg", v=str(p["amount"])),
            style="primary" if p["popular"] else None,
        )
        for p in pkgs
    ]
    grid = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    await show(
        ev,
        t(lang, "stars_title", who=who_label(lang, flow, user)),
        kb(
            *grid,
            btn(t(lang, "b_other_amount"), Fl(s="custom")),
            [btn(t(lang, "b_back"), Fl(s="back_who")), btn(t(lang, "b_cancel"), Menu(a="home"), style="danger")],
        ),
    )


async def _quote(svc: Services, user: User, flow: dict) -> tuple[Quote, str | None]:  # type: ignore[type-arg]
    """Quote with promo if valid; returns (quote, promo_error)."""
    product = ProductType(flow["product"])

    async def base(promo: PromoCode | None = None) -> Quote:
        if product == ProductType.PREMIUM:
            plan = await svc.session.get(PremiumPlan, flow["plan_id"])
            assert plan is not None
            return await svc.pricing.quote_premium(plan, promo)
        return await svc.pricing.quote_stars(flow["stars"], promo)

    plain = await base()
    if flow.get("promo"):
        try:
            promo = await PromoService(svc.session).validate(flow["promo"], user.id, product, plain.price_usd)
            return await base(promo), None
        except AppError as exc:
            return plain, exc.message
    return plain, None


async def screen_summary(
    ev: Message | CallbackQuery, svc: Services, state: FSMContext, user: User, lang: str, note: str = ""
) -> None:
    flow = _flow(await state.get_data())
    q, promo_err = await _quote(svc, user, flow)
    what = (
        t(lang, "what_prem", months=flow["months"])
        if flow["product"] == "premium"
        else t(lang, "what_star", amount=stars_fmt(flow["stars"]))
    )
    promo_line = t(lang, "promo_line", discount=usd(q.discount_usd)) if q.discount_usd else ""
    text = t(
        lang,
        "summary",
        what=what,
        who=who_label(lang, flow, user),
        price=usd(q.price_usd),
        uzs=uzs(q.price_uzs),
        promo=promo_line,
    )
    if promo_err:
        text = t(lang, "promo_bad", why=promo_err) + "\n\n" + text
        flow.pop("promo", None)
        await state.update_data(flow=flow)
    methods = []
    no_username = (
        flow.get("rtype") == "self" and not user.username or flow.get("rtype") == "other" and not flow.get("ruser")
    )
    ton_ready = bool(await svc.settings.get("hot_wallet.address")) and bool(
        await svc.settings.get("payments.ton.enabled")
    )
    if ton_ready and not no_username:
        methods.append(btn(t(lang, "m_ton", amount=ton(q.price_ton)), Fl(s="pay", v="ton")))
    if (
        flow["product"] == "premium"
        and await svc.settings.get("payments.stars.enabled")
        and q.price_xtr > 0
        and get_settings().bot_token.get_secret_value()
    ):
        methods.append(
            btn(t(lang, "m_stars", amount=stars_fmt(q.price_xtr).replace(" ⭐", "")), Fl(s="pay", v="stars"))
        )
    if await svc.settings.get("payments.balance.enabled") and not no_username:
        if user.balance_usd >= q.price_usd:
            methods.append(btn(t(lang, "m_balance", amount=usd(q.price_usd)), Fl(s="pay", v="balance")))
        else:
            methods.append(btn(t(lang, "m_balance_low"), Fl(s="lowbal")))
    if not methods:
        text += "\n\n" + t(lang, "ton_unconfigured")
    back = Fl(s="back_plans") if flow["product"] == "premium" else Fl(s="back_pkgs")
    await show(
        ev,
        text + note,
        kb(
            *methods,
            btn(t(lang, "b_promo"), Fl(s="promo")),
            [btn(t(lang, "b_back"), back), btn(t(lang, "b_cancel"), Menu(a="home"), style="danger")],
        ),
    )


@router.callback_query(Fl.filter())
async def on_flow(
    cb: CallbackQuery, callback_data: Fl, state: FSMContext, user: User, lang: str, svc: Services, rt: Runtime
) -> None:
    s, v = callback_data.s, callback_data.v
    flow = _flow(await state.get_data())
    if not flow and s not in ("soon",):
        await toast(cb)
        await show(cb, t(lang, "use_menu"), kb(btn(t(lang, "b_home"), Menu(a="home"))))
        return
    if s == "soon":
        await toast(cb, t(lang, "plan_soon_toast"), alert=True)
        return
    if s == "lowbal":
        await toast(cb, t(lang, "balance_low_toast"), alert=True)
        return
    await toast(cb)
    if s in ("who", "back_who"):
        if s == "back_who":
            await state.set_state(None)
            return await screen_who(cb, state, user, lang)
        if v == "self":
            if flow["product"] == "stars" and not user.username:
                return await toast(cb, t(lang, "no_username_note"), alert=True)
            flow.update(rtype="self", ruser=user.username, rid=user.id, rname=user.first_name)
            await state.update_data(flow=flow)
            return await (screen_plans if flow["product"] == "premium" else screen_packages)(cb, svc, state, user, lang)
        flow.update(rtype="other")
        await state.update_data(flow=flow)
        await state.set_state(Flow.recipient_username)
        assert isinstance(cb.message, Message)
        await show(cb, t(lang, "ask_username"), kb(btn(t(lang, "b_cancel"), Menu(a="home"), style="danger")))
        await cb.message.answer(
            "👇",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(
                            text=t(lang, "b_contact"),
                            request_users=KeyboardButtonRequestUsers(
                                request_id=1, user_is_bot=False, request_username=True, request_name=True
                            ),
                        )
                    ],
                    [KeyboardButton(text=t(lang, "b_cancel"))],
                ],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
    elif s == "rec_ok":
        await state.set_state(None)
        await (screen_plans if flow["product"] == "premium" else screen_packages)(cb, svc, state, user, lang)
    elif s == "plan":
        plan = await svc.session.get(PremiumPlan, int(v))
        if plan is None:
            return
        flow.update(plan_id=plan.id, months=plan.months)
        await state.update_data(flow=flow)
        await screen_summary(cb, svc, state, user, lang)
    elif s == "pkg":
        flow.update(stars=int(v))
        await state.update_data(flow=flow)
        await screen_summary(cb, svc, state, user, lang)
    elif s == "custom":
        await state.set_state(Flow.stars_amount)
        mx = int(await svc.settings.get("pricing.stars.max_amount"))
        await show(
            cb, t(lang, "ask_stars_amount", max=mx), kb(btn(t(lang, "b_cancel"), Menu(a="home"), style="danger"))
        )
    elif s == "back_plans":
        await screen_plans(cb, svc, state, user, lang)
    elif s == "back_pkgs":
        await screen_packages(cb, svc, state, user, lang)
    elif s == "promo":
        await state.set_state(Flow.promo)
        await show(cb, t(lang, "ask_promo"), kb(btn(t(lang, "b_back"), Fl(s="back_summary"))))
    elif s == "back_summary":
        await state.set_state(None)
        await screen_summary(cb, svc, state, user, lang)
    elif s == "pay":
        await create_and_show_order(cb, svc, rt, state, user, lang, PaymentMethod(v))


@router.message(Flow.recipient_username, F.users_shared)
async def on_users_shared(m: Message, state: FSMContext, user: User, lang: str, svc: Services) -> None:
    shared = m.users_shared.users[0] if m.users_shared else None
    flow = _flow(await state.get_data())
    tmp = await m.answer("✅", reply_markup=ReplyKeyboardRemove())
    await tmp.delete()
    if shared is None:
        return
    name = " ".join(x for x in (shared.first_name, shared.last_name) if x) or None
    flow.update(rtype="other", ruser=shared.username, rid=shared.user_id, rname=name)
    if flow["product"] == "stars" and not shared.username:
        await m.answer(t(lang, "username_bad"))
        return
    await state.update_data(flow=flow)
    await _recipient_card(m, lang, flow, name or str(shared.user_id))


async def _recipient_card(m: Message, lang: str, flow: dict, name: str) -> None:  # type: ignore[type-arg]
    markup = kb(
        btn(t(lang, "b_continue"), Fl(s="rec_ok"), style="success"),
        [
            btn(t(lang, "b_other_username"), Fl(s="who", v="other")),
            btn(t(lang, "b_cancel"), Menu(a="home"), style="danger"),
        ],
    )
    await m.answer(t(lang, "username_found", name=name, u=flow.get("ruser") or flow.get("rid")), reply_markup=markup)


@router.message(Flow.recipient_username, F.text)
async def on_recipient_username(m: Message, state: FSMContext, user: User, lang: str, svc: Services) -> None:
    flow = _flow(await state.get_data())
    try:
        username = normalize_username(m.text or "")
    except AppError:
        await m.answer(t(lang, "username_bad"))
        return
    info = await resolve_recipient(svc, username, flow.get("product", "premium"), flow.get("months") or 3)
    if not info["found"]:
        await m.answer(t(lang, "username_notfound", u=username))
        return
    if not info["can_receive"]:
        await m.answer(t(lang, "username_cannot"))
        return
    tmp = await m.answer("✅", reply_markup=ReplyKeyboardRemove())
    await tmp.delete()
    flow.update(rtype="other", ruser=username, rid=None, rname=info.get("name"))
    await state.update_data(flow=flow)
    await _recipient_card(m, lang, flow, info.get("name") or username)


@router.message(Flow.stars_amount, F.text)
async def on_custom_stars(m: Message, state: FSMContext, user: User, lang: str, svc: Services) -> None:
    mx = int(await svc.settings.get("pricing.stars.max_amount"))
    txt = (m.text or "").replace(" ", "")
    if not txt.isdigit() or not 50 <= int(txt) <= mx:
        await m.answer(t(lang, "bad_number"))
        return
    flow = _flow(await state.get_data())
    flow["stars"] = int(txt)
    await state.update_data(flow=flow)
    await state.set_state(None)
    await screen_summary(m, svc, state, user, lang)


@router.message(Flow.promo, F.text)
async def on_promo(m: Message, state: FSMContext, user: User, lang: str, svc: Services) -> None:
    flow = _flow(await state.get_data())
    flow["promo"] = (m.text or "").strip()
    await state.update_data(flow=flow)
    await state.set_state(None)
    await screen_summary(m, svc, state, user, lang)


async def create_and_show_order(
    cb: CallbackQuery, svc: Services, rt: Runtime, state: FSMContext, user: User, lang: str, method: PaymentMethod
) -> None:
    flow = _flow(await state.get_data())
    req = CreateOrderRequest(
        product_type=ProductType(flow["product"]),
        payment_method=method,
        plan_id=flow.get("plan_id"),
        stars_amount=flow.get("stars"),
        recipient_type=RecipientType(flow["rtype"]),
        recipient_username=flow.get("ruser") if flow["rtype"] == "other" else None,
        recipient_user_id=flow.get("rid") if flow["rtype"] == "other" else None,
        recipient_name=flow.get("rname"),
        promo_code=flow.get("promo"),
    )
    try:
        res = await svc.checkout.create_order(user, req)
    except AppError as exc:
        msg = t(lang, f"err_{exc.code}")
        await toast(cb, msg if not msg.startswith("err_") else t(lang, "error_generic"), alert=True)
        return
    await state.clear()
    assert res.order is not None
    await present_payment(cb, svc, rt, user, lang, res, res.order)


async def present_payment(
    ev: CallbackQuery | Message,
    svc: Services,
    rt: Runtime,
    user: User,
    lang: str,
    res: CheckoutResult,
    order: Order | None,
) -> None:
    pay = res.payment
    ttl = int(await svc.settings.get("payments.invoice_ttl_minutes"))
    if pay.method == PaymentMethod.TON:
        ex = res.instructions.extra
        text = t(lang, "ton_screen", amount=ton(pay.amount), address=ex["address"], comment=ex["comment"], minutes=ttl)
        markup = kb(
            btn(
                t(lang, "b_pay_wallet"),
                web_app=webapp_url(f"/checkout/{order.public_id if order else pay.public_id}"),
                style="success",
            )
            if get_settings().webapp_url.startswith("https://")
            else None,
            [
                btn(t(lang, "b_copy_addr"), copy=ex["address"]),
                btn(t(lang, "b_copy_comment"), copy=ex["comment"]),
                btn(t(lang, "b_copy_amount"), copy=ton(pay.amount)),
            ],
            btn(t(lang, "b_tonkeeper"), url=ex["tonkeeper_link"]),
            btn(t(lang, "b_check"), Pay(a="check", id=pay.public_id), style="primary"),
            btn(t(lang, "b_cancel_order"), Pay(a="cancel", id=pay.public_id), style="danger"),
        )
        msg = await show(ev, text, markup)
        if order is not None:
            order.bot_message_id = msg.message_id
    elif pay.method == PaymentMethod.STARS:
        gw = rt.stars
        assert gw is not None
        chat_id = user.id
        if order is not None:
            title = (
                t(lang, "invoice_title_prem", months=order.plan_months)
                if order.plan_months
                else t(lang, "what_star", amount=stars_fmt(order.stars_amount or 0))
            )
            desc = t(lang, "invoice_desc", oid=order.public_id)
        else:
            title, desc = t(lang, "invoice_title_topup"), f"{pay.public_id} · Soft-tg-Market"
        await gw.send_invoice(chat_id, title, desc, pay.public_id, int(pay.amount))
        await show(ev, t(lang, "stars_invoice_hint"), kb(btn(t(lang, "b_home"), Menu(a="home"))))
    else:  # balance
        assert order is not None
        msg = await show(ev, t(lang, "order_status_paid", oid=order.public_id), None)
        order.bot_message_id = msg.message_id


@router.callback_query(Pay.filter())
async def on_pay(
    cb: CallbackQuery,
    callback_data: Pay,
    state: FSMContext,
    user: User,
    lang: str,
    role: object,
    svc: Services,
    rt: Runtime,
    session: AsyncSession,
) -> None:
    from app.services.payment_service import PaymentService

    ps = PaymentService(svc.session, svc.settings, svc.notifier)
    pay = await ps.by_public_id(callback_data.id, user.id)
    if pay is None:
        await toast(cb, t(lang, "order_closed"), alert=True)
        return
    if callback_data.a == "check":
        from app.workers.jobs import ton_watcher

        await session.commit()
        try:
            await ton_watcher(rt)
        except Exception as exc:  # noqa: BLE001
            log.warning("manual_check_failed", error=str(exc))
        session.expire_all()
        pay = await ps.by_public_id(callback_data.id, user.id)
        assert pay is not None
        if pay.status.value == "confirmed":
            await toast(cb, "✅")
        else:
            await toast(cb, t(lang, "check_pending"), alert=True)
        return
    # cancel / cancel_stars
    await toast(cb)
    if pay.order_id:
        order = await OrderService(svc.session).get(pay.order_id)
        try:
            await svc.checkout.cancel(order, user.id)
        except AppError:
            await toast(cb, t(lang, "order_closed"), alert=True)
            return
    await show(cb, t(lang, "order_cancelled"), kb(btn(t(lang, "b_home"), Menu(a="home"))))


# ======================= wallet =======================
async def screen_wallet(ev: Message | CallbackQuery, svc: Services, user: User, lang: str) -> None:
    ton_usd, usd_uzs = await svc.rates.ton_usd(), await svc.rates.usd_uzs()
    text = t(
        lang,
        "wallet",
        usd=usd(user.balance_usd),
        uzs=uzs(user.balance_usd * usd_uzs),
        ton=ton(user.balance_usd / ton_usd),
    )
    rows = [
        btn(t(lang, "b_topup"), Wal(a="topup"), style="success"),
        [
            btn(t(lang, "b_history"), Wal(a="hist")),
            btn(t(lang, "b_app"), web_app=webapp_url("/wallet"), style="primary"),
        ]
        if get_settings().webapp_url.startswith("https://")
        else btn(t(lang, "b_history"), Wal(a="hist")),
        btn(t(lang, "b_back"), Menu(a="home")),
    ]
    await show(ev, text, kb(*rows))


@router.callback_query(Wal.filter())
async def on_wallet(
    cb: CallbackQuery, callback_data: Wal, state: FSMContext, user: User, lang: str, svc: Services, rt: Runtime
) -> None:
    await toast(cb)
    a = callback_data.a
    if a == "open":
        await screen_wallet(cb, svc, user, lang)
    elif a == "hist":
        per = 8
        txs = await BalanceService(svc.session).history(user.id, per + 1, callback_data.page * per)
        lines = [
            f"{'+' if r.amount_usd > 0 else '−'}{abs(r.amount_usd):.2f} $ · {r.type.value} · {dt(r.created_at)}"
            for r in txs[:per]
        ]
        text = (
            t(lang, "history_title", page=callback_data.page + 1)
            + "\n\n"
            + ("\n".join(lines) if lines else t(lang, "history_empty"))
        )
        nav = []
        if callback_data.page > 0:
            nav.append(btn("◀️", Wal(a="hist", page=callback_data.page - 1)))
        if len(txs) > per:
            nav.append(btn("▶️", Wal(a="hist", page=callback_data.page + 1)))
        await show(cb, text, kb(nav, btn(t(lang, "b_back"), Wal(a="open"))))
    elif a == "topup":
        rows = []
        if await svc.settings.get("payments.ton.enabled") and await svc.settings.get("hot_wallet.address"):
            rows.append(btn("💎 TON", Wal(a="tm", v="ton")))
        if await svc.settings.get("payments.topup.stars.enabled") and await svc.settings.get("payments.stars.enabled"):
            rows.append(btn("⭐ Stars", Wal(a="tm", v="stars")))
        await show(
            cb,
            t(lang, "topup_method") if rows else t(lang, "ton_unconfigured"),
            kb([*rows], btn(t(lang, "b_back"), Wal(a="open"))),
        )
    elif a == "tm":
        await state.update_data(topup_method=callback_data.v)
        amounts = [btn(f"{x} $", Wal(a="amt", v=str(x))) for x in TOPUP_AMOUNTS]
        await show(
            cb,
            t(lang, "topup_amount"),
            kb(
                amounts[:3],
                amounts[3:],
                btn(t(lang, "b_other_sum"), Wal(a="custom")),
                btn(t(lang, "b_back"), Wal(a="topup")),
            ),
        )
    elif a == "custom":
        await state.set_state(Flow.topup_amount)
        lo, hi = await svc.settings.get("pricing.topup.min_usd"), await svc.settings.get("pricing.topup.max_usd")
        await show(cb, t(lang, "ask_topup_amount", min=lo, max=hi), kb(btn(t(lang, "b_back"), Wal(a="topup"))))
    elif a == "amt":
        await create_topup(cb, state, svc, rt, user, lang, D(callback_data.v))


async def create_topup(
    ev: CallbackQuery | Message, state: FSMContext, svc: Services, rt: Runtime, user: User, lang: str, amount: Decimal
) -> None:
    method = PaymentMethod((await state.get_data()).get("topup_method", "ton"))
    try:
        res = await svc.checkout.create_topup(user, amount, method)
    except AppError as exc:
        text = t(lang, f"err_{exc.code}")
        await (ev.answer(text) if isinstance(ev, Message) else toast(ev, text, alert=True))
        return
    await state.clear()
    target = ev if isinstance(ev, CallbackQuery) else ev
    await present_payment(target, svc, rt, user, lang, res, None)


@router.message(Flow.topup_amount, F.text)
async def on_topup_amount(m: Message, state: FSMContext, user: User, lang: str, svc: Services, rt: Runtime) -> None:
    try:
        amount = D((m.text or "").replace(",", ".").replace("$", "").strip())
    except (InvalidOperation, TypeError):
        await m.answer(t(lang, "bad_number"))
        return
    await create_topup(m, state, svc, rt, user, lang, amount)


# ======================= orders / referral / settings / help =======================
async def screen_orders(ev: Message | CallbackQuery, svc: Services, user: User, lang: str, page: int) -> None:
    per = 6
    rows = await OrderService(svc.session).list_for_user(user.id, None, per + 1, page * per)
    if not rows:
        await show(
            ev, t(lang, "orders_title") + "\n\n" + t(lang, "orders_empty"), kb(btn(t(lang, "b_back"), Menu(a="home")))
        )
        return
    buttons = [
        btn(f"{STATUS_ICON[o.status.value]} {o.public_id} · {order_what(lang, o)}", Ord(a="view", id=o.public_id))
        for o in rows[:per]
    ]
    nav = []
    if page > 0:
        nav.append(btn("◀️", Ord(a="list", page=page - 1)))
    if len(rows) > per:
        nav.append(btn("▶️", Ord(a="list", page=page + 1)))
    await show(ev, t(lang, "orders_title"), kb(*buttons, nav, btn(t(lang, "b_back"), Menu(a="home"))))


async def order_view(ev: Message | CallbackQuery, svc: Services, user: User, lang: str, public_id: str) -> None:
    try:
        o = await OrderService(svc.session).by_public_id(public_id, user.id)
    except AppError:
        await show(ev, t(lang, "order_closed"), kb(btn(t(lang, "b_home"), Menu(a="home"))))
        return
    text = t(
        lang,
        "order_card",
        oid=o.public_id,
        status=t(lang, f"st_{o.status.value}"),
        what=order_what(lang, o),
        who=who_label(lang, o, user),
        price=usd(o.price_usd),
        date=dt(o.created_at),
    )
    rows = [btn(t(lang, "b_repeat"), Ord(a="repeat", id=o.public_id), style="success")]
    if o.status in (OrderStatus.FAILED, OrderStatus.NEEDS_REVIEW, OrderStatus.REFUNDED):
        support = await svc.settings.get("bot.support_username")
        if support:
            rows.append(btn(t(lang, "b_support"), url=f"https://t.me/{support}", style="primary"))
    await show(ev, text, kb(*rows, btn(t(lang, "b_back"), Ord(a="list"))))


@router.callback_query(Ord.filter())
async def on_orders(
    cb: CallbackQuery, callback_data: Ord, state: FSMContext, user: User, lang: str, svc: Services
) -> None:
    await toast(cb)
    if callback_data.a == "list":
        await screen_orders(cb, svc, user, lang, callback_data.page)
    elif callback_data.a == "view":
        await order_view(cb, svc, user, lang, callback_data.id)
    elif callback_data.a == "repeat":
        o = await OrderService(svc.session).by_public_id(callback_data.id, user.id)
        flow = {
            "product": o.product_type.value,
            "rtype": o.recipient_type.value,
            "ruser": o.recipient_username,
            "rid": o.recipient_user_id if o.recipient_type.value == "other" else user.id,
            "rname": o.recipient_name,
        }
        if o.product_type == ProductType.PREMIUM:
            flow.update(plan_id=o.plan_id, months=o.plan_months)
        else:
            flow.update(stars=o.stars_amount)
        await state.update_data(flow=flow)
        await screen_summary(cb, svc, state, user, lang)


async def screen_referral(ev: Message | CallbackQuery, svc: Services, user: User, lang: str) -> None:
    stats = await ReferralService(svc.session, svc.settings, svc.notifier).stats(user.id)
    bot = get_settings().bot_username
    link = f"https://t.me/{bot}?start=ref_{user.id}" if bot else f"ref_{user.id}"
    text = t(
        lang,
        "referral",
        percent=await svc.settings.get("referral.percent"),
        link=link,
        invited=stats["invited"],
        earned=usd(str(stats["earned_usd"])),
    )
    from urllib.parse import quote

    share = f"https://t.me/share/url?url={quote(link)}&text={quote(t(lang, 'share_text'))}"
    await show(
        ev,
        text,
        kb(
            btn(t(lang, "b_share"), url=share, style="success"),
            btn(t(lang, "b_copy_link"), copy=link),
            btn(t(lang, "b_back"), Menu(a="home")),
        ),
    )


async def screen_settings(ev: Message | CallbackQuery, user: User, lang: str) -> None:
    mkt = t(lang, "b_mkt_off") if user.marketing_opt_out else t(lang, "b_mkt_on")
    await show(
        ev,
        t(lang, "settings"),
        kb(
            btn(f"{t(lang, 'b_lang')}: {lang.upper()}", Set(a="lang")),
            btn(mkt, Set(a="mkt")),
            btn(t(lang, "b_back"), Menu(a="home")),
        ),
    )


async def help_screen(ev: Message | CallbackQuery, svc: Services, lang: str) -> None:
    support = await svc.settings.get("bot.support_username")
    await show(
        ev,
        t(lang, "help"),
        kb(
            btn(t(lang, "b_support"), url=f"https://t.me/{support}", style="primary") if support else None,
            btn(t(lang, "b_back"), Menu(a="home")),
        ),
    )


@router.message(F.text & ~F.text.startswith("/"))
async def fallback(m: Message, user: User, lang: str, role: object) -> None:
    await m.answer(t(lang, "use_menu"))
    await menu_screen(m, user, lang, role, new=True)
