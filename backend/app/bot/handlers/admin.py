"""Admin panel inside the bot (Uzbek only). Mirrors the Mini App admin: every action is audited."""

import json
import secrets
from datetime import timedelta
from decimal import InvalidOperation
from typing import Any

import structlog
from aiogram import Bot, F, Router
from aiogram.filters import BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy import func, select

from app.api.runtime import Runtime, Services
from app.bot.callbacks import Adm, Cf, Menu
from app.bot.helpers import dt, show, toast
from app.bot.keyboards import btn, kb
from app.bot.states import Adm as St
from app.core.config import get_settings
from app.core.enums import (
    AdminRole,
    BroadcastStatus,
    ExpenseCategory,
    OrderStatus,
    ProductScope,
    PromoType,
)
from app.core.errors import AppError
from app.core.money import D
from app.core.redis import get_redis
from app.core.timeutil import now_utc, today_local
from app.models import Channel, Order, PremiumPlan, PromoCode, StarsTransaction, UnmatchedTonTx, User
from app.services.admin_service import AdminService
from app.services.analytics_service import AnalyticsService, resolve_period
from app.services.balance_service import BalanceService
from app.services.broadcast_service import BroadcastService
from app.services.export_service import ExportService
from app.services.order_service import OrderService
from app.services.report_service import format_stats
from app.services.user_service import UserService

log = structlog.get_logger()
router = Router(name="admin")
RANK = {AdminRole.SUPPORT: 1, AdminRole.ADMIN: 2, AdminRole.OWNER: 3}


class IsStaff(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery, role: AdminRole | None = None) -> bool:
        return role is not None


router.message.filter(IsStaff())
router.callback_query.filter(IsStaff())


def has(role: AdminRole | None, minimum: AdminRole) -> bool:
    return role is not None and RANK[role] >= RANK[minimum]


async def need(cb: CallbackQuery | Message, role: AdminRole | None, minimum: AdminRole) -> bool:
    if has(role, minimum):
        return True
    if isinstance(cb, CallbackQuery):
        await cb.answer("⛔️ Ruxsat yo'q", show_alert=True)
    else:
        await cb.answer("⛔️ Ruxsat yo'q")
    return False


BACK = btn("« Admin panel", Adm(sec="panel"))


def back(sec: str, text: str = "« Orqaga") -> Any:
    return btn(text, Adm(sec=sec))


# ---------------- confirmations ----------------
async def ask_confirm(
    ev: Message | CallbackQuery, text: str, action: str, params: dict[str, Any], actor: int, danger: bool = True
) -> None:
    token = secrets.token_urlsafe(6)
    await get_redis().set(f"cf:{token}", json.dumps({"action": action, "params": params, "actor": actor}), ex=300)
    yes = btn("✅ Ha, tasdiqlash", Cf(token=token, yes=True), style="danger" if danger else "success")
    await show(ev, text + "\n\n<i>Tasdiqlaysizmi?</i>", kb(yes, btn("Yo'q", Cf(token=token, yes=False))))


# ---------------- panel ----------------
async def panel_text(svc: Services) -> str:
    a = AnalyticsService(svc.session)
    d = await a.dashboard(resolve_period("today"))
    c, tot = d["current"], d["totals"]
    lines = [
        f"🛠 <b>Admin panel</b>\n\n📊 <b>Bugun</b> ({today_local():%d.%m.%Y})",
        f"💵 Tushum: {c['cash_in_usd']:.2f} $ · Sotuv: {c['revenue_usd']:.2f} $",
        f"📈 Sof foyda: {c['net_profit_usd']:.2f} $",
        f"📦 Buyurtmalar: {c['orders_completed']} (❌ {c['orders_failed']} · ↩️ {c['orders_refunded']})",
        f"👥 Yangi: +{c['new_users']} · Faol: {c['active_users']}",
    ]
    try:
        hw = svc.hot_wallet()
        if await svc.settings.get("hot_wallet.address"):
            lines.append(f"\n💎 Hot wallet: {await hw.balance():.2f} TON")
    except Exception:  # noqa: BLE001
        lines.append("\n💎 Hot wallet: — (TonAPI javob bermadi)")
    stars = await get_redis().get("stars:balance")
    if stars is not None:
        lines.append(f"⭐ Stars balans: {int(stars):,}".replace(",", " "))
    if tot["needs_review"]:
        lines.append(f"⚠️ Tekshirish kerak: <b>{tot['needs_review']}</b> ta buyurtma")
    return "\n".join(lines)


async def screen_panel(ev: Message | CallbackQuery, svc: Services, role: AdminRole, new: bool = False) -> None:
    review = (await AnalyticsService(svc.session).dashboard(resolve_period("today")))["totals"]["needs_review"]
    rows: list[Any] = []
    if get_settings().webapp_url.startswith("https://"):
        rows.append(btn("🚀 Admin Mini App", web_app=get_settings().webapp_url.rstrip("/") + "/admin", style="primary"))
    if has(role, AdminRole.ADMIN):
        rows.append(
            [
                btn("📊 Statistika", Adm(sec="stats")),
                btn(f"📦 Buyurtmalar{f' (⚠️{review})' if review else ''}", Adm(sec="orders")),
            ]
        )
    else:
        rows.append([btn(f"📦 Buyurtmalar{f' (⚠️{review})' if review else ''}", Adm(sec="orders"))])
    rows.append(
        [btn("👥 Foydalanuvchilar", Adm(sec="users"))]
        + ([btn("💰 Moliya", Adm(sec="fin"))] if has(role, AdminRole.ADMIN) else [])
    )
    if has(role, AdminRole.ADMIN):
        rows += [
            [btn("🏷 Narxlar", Adm(sec="price")), btn("💳 To'lov usullari", Adm(sec="methods"))],
            [btn("📣 Xabar yuborish", Adm(sec="bc")), btn("🎟 Promokodlar", Adm(sec="promo"))],
            [btn("🤝 Referal", Adm(sec="ref")), btn("📢 Majburiy obuna", Adm(sec="chan"))],
            [btn("⚙️ Sozlamalar", Adm(sec="set"))]
            + ([btn("👮 Adminlar", Adm(sec="admins"))] if role == AdminRole.OWNER else []),
        ]
    rows.append([btn("🔄 Yangilash", Adm(sec="panel")), btn("« Bosh menyu", Menu(a="home"))])
    await show(ev, await panel_text(svc), kb(*rows), new=new)


@router.message(Command("admin"))
async def cmd_admin(m: Message, svc: Services, role: AdminRole, state: FSMContext) -> None:
    await state.clear()
    await screen_panel(m, svc, role, new=True)


@router.message(Command("stats"))
async def cmd_stats(m: Message, svc: Services, role: AdminRole) -> None:
    if not await need(m, role, AdminRole.ADMIN):
        return
    arg = (m.text or "").split(maxsplit=1)[1] if m.text and " " in m.text else "today"
    await screen_stats(m, svc, arg if arg in ("today", "yesterday", "week", "month", "year") else "today")


@router.message(Command("order"))
async def cmd_order(m: Message, svc: Services, role: AdminRole) -> None:
    arg = (m.text or "").split(maxsplit=1)[1].strip() if m.text and " " in m.text else ""
    if arg:
        await screen_order(m, svc, role, arg)


@router.message(Command("find"))
async def cmd_find(m: Message, svc: Services, role: AdminRole) -> None:
    arg = (m.text or "").split(maxsplit=1)[1].strip() if m.text and " " in m.text else ""
    if arg:
        await user_search_results(m, svc, arg)


@router.message(Command("addbalance", "subbalance"))
async def cmd_balance(m: Message, svc: Services, role: AdminRole, user: User) -> None:
    if not await need(m, role, AdminRole.ADMIN):
        return
    parts = (m.text or "").split(maxsplit=3)
    try:
        uid, amount = int(parts[1]), D(parts[2])
    except (IndexError, ValueError, InvalidOperation):
        await m.answer("Format: <code>/addbalance &lt;id&gt; &lt;usd&gt; [izoh]</code>")
        return
    if (m.text or "").startswith("/subbalance"):
        amount = -abs(amount)
    comment = parts[3] if len(parts) > 3 else None
    await ask_confirm(
        m,
        f"💼 <code>{uid}</code> balansiga <b>{amount:+.2f} $</b>",
        "balance",
        {"user_id": uid, "amount": str(amount), "comment": comment},
        user.id,
        danger=amount < 0,
    )


@router.message(Command("ban", "unban"))
async def cmd_ban(m: Message, svc: Services, role: AdminRole, user: User) -> None:
    if not await need(m, role, AdminRole.ADMIN):
        return
    parts = (m.text or "").split(maxsplit=2)
    if len(parts) < 2 or not parts[1].isdigit():
        await m.answer("Format: <code>/ban &lt;id&gt; [sabab]</code>")
        return
    unban = (m.text or "").startswith("/unban")
    await ask_confirm(
        m,
        f"{'✅ Blokdan chiqarish' if unban else '⛔️ Bloklash'}: <code>{parts[1]}</code>",
        "unban" if unban else "ban",
        {"user_id": int(parts[1]), "reason": parts[2] if len(parts) > 2 else None},
        user.id,
        danger=not unban,
    )


@router.message(Command("maintenance"))
async def cmd_maint(m: Message, svc: Services, role: AdminRole, user: User) -> None:
    if not await need(m, role, AdminRole.ADMIN):
        return
    arg = (m.text or "").split(maxsplit=1)[1].strip() if m.text and " " in m.text else ""
    await svc.settings.set("bot.maintenance", arg == "on", user.id)
    await m.answer(f"🛠 Texnik ishlar: {'YOQILDI' if arg == 'on' else 'o`chirildi'}")


@router.message(Command("withdraw"))
async def cmd_withdraw(m: Message, svc: Services, role: AdminRole, user: User, state: FSMContext) -> None:
    if not await need(m, role, AdminRole.OWNER):
        return
    arg = (m.text or "").split(maxsplit=1)[1].strip() if m.text and " " in m.text else ""
    if arg:
        await withdraw_confirm(m, svc, user, arg)
    else:
        await screen_fin(m, svc, role)


@router.message(Command("health"))
async def cmd_health(m: Message, svc: Services, role: AdminRole, rt: Runtime) -> None:
    await m.answer(await health_text(svc, rt))


@router.message(Command("prices"))
async def cmd_prices(m: Message, svc: Services, role: AdminRole) -> None:
    if await need(m, role, AdminRole.ADMIN):
        await screen_price(m, svc)


@router.message(Command("finance"))
async def cmd_fin(m: Message, svc: Services, role: AdminRole) -> None:
    if await need(m, role, AdminRole.ADMIN):
        await screen_fin(m, svc, role)


@router.message(Command("broadcast"))
async def cmd_bc(m: Message, svc: Services, role: AdminRole, state: FSMContext) -> None:
    if await need(m, role, AdminRole.ADMIN):
        await state.set_state(St.bc_content)
        await m.answer(
            "📣 Xabarni yuboring (matn, rasm, video yoki GIF — formatlash saqlanadi).\nBekor qilish: /cancel"
        )


async def health_text(svc: Services, rt: Runtime) -> str:
    redis = get_redis()
    hb = await redis.get("worker:heartbeat")
    ok = "✅"
    lines = [
        f"🩺 <b>Tizim holati</b>\nDB {ok}",
        f"Redis {ok if await redis.ping() else '❌'}",
        f"Worker {'✅ ' + str(hb)[11:19] if hb else '❌ (heartbeat yo`q)'}",
    ]
    try:
        if await svc.settings.get("hot_wallet.address"):
            await svc.hot_wallet().balance()
            lines.append("TonAPI ✅")
        else:
            lines.append("TonAPI — hot wallet sozlanmagan")
    except Exception as exc:  # noqa: BLE001
        lines.append(f"TonAPI ❌ {str(exc)[:60]}")
    frag = bool(await svc.settings.get("fragment.cookies"))
    lines.append(f"Fragment cookie: {'✅ kiritilgan' if frag else '— kiritilmagan'}")
    if rt.bot is not None:
        try:
            info = await rt.bot.get_webhook_info()
            lines.append(f"Webhook: {'✅' if info.url else '— (polling)'} · navbat {info.pending_update_count}")
        except Exception:  # noqa: BLE001
            lines.append("Webhook ❌")
    lines.append(f"Texnik ishlar: {'🛠 YOQILGAN' if await svc.settings.get('bot.maintenance') else 'o`chiq'}")
    return "\n".join(lines)


# ---------------- callback router ----------------
@router.callback_query(Adm.filter())
async def on_admin(
    cb: CallbackQuery, callback_data: Adm, svc: Services, role: AdminRole, user: User, state: FSMContext, rt: Runtime
) -> None:
    await toast(cb)
    sec, act, id_, page = callback_data.sec, callback_data.act, callback_data.id, callback_data.page
    if sec != "panel" and sec not in ("orders", "users") and not await need(cb, role, AdminRole.ADMIN):
        return
    if act == "open" or sec in ("panel",):
        await state.set_state(None)
    handler = SECTIONS.get(sec)
    if sec == "panel":
        await screen_panel(cb, svc, role)
    elif handler:
        await handler(cb, svc, role, user, state, rt, act, id_, page)


# ---------------- stats ----------------
async def screen_stats(ev: Message | CallbackQuery, svc: Services, period: str) -> None:
    a = AnalyticsService(svc.session)
    d = await a.dashboard(resolve_period(period))
    titles = {"today": "Bugun", "yesterday": "Kecha", "week": "Hafta", "month": "Oy", "year": "Yil"}
    text = format_stats(f"Statistika · {titles.get(period, period)}", d, await a.dau_wau_mau())
    row = [
        btn(v, Adm(sec="stats", id=k), style="primary" if k == period else None)
        for k, v in titles.items()
        if k != "yesterday"
    ]
    webapp = get_settings().webapp_url
    rows = [
        row,
        [btn("Kecha", Adm(sec="stats", id="yesterday")), btn("📅 Ixtiyoriy davr", Adm(sec="stats", act="custom"))],
    ]
    if webapp.startswith("https://"):
        rows.append([btn("📈 Grafiklar", web_app=f"{webapp.rstrip('/')}/admin/stats?period={period}", style="primary")])
    rows.append(
        [
            btn("📥 Excel", Adm(sec="stats", act="xlsx", id=period)),
            btn("🏆 Top xaridorlar", Adm(sec="stats", act="top", id=period)),
        ]
    )
    rows.append([BACK])
    await show(ev, text, kb(*rows))


async def sec_stats(
    cb: CallbackQuery,
    svc: Services,
    role: AdminRole,
    user: User,
    state: FSMContext,
    rt: Runtime,
    act: str,
    id_: str,
    page: int,
) -> None:
    period = id_ or "today"
    if act == "xlsx":
        data = await ExportService(svc.session).export_period(resolve_period(period))
        assert isinstance(cb.message, Message)
        await cb.message.answer_document(BufferedInputFile(data, f"stats_{period}.xlsx"))
        return
    if act == "top":
        p = resolve_period(period)
        rows = await AnalyticsService(svc.session).top_buyers(p.start, p.end)
        text = "🏆 <b>Top xaridorlar</b>\n\n" + (
            "\n".join(
                f"{i + 1}. {r['name'] or r['username'] or r['id']} — {r['spent_usd']} $ ({r['orders']})"
                for i, r in enumerate(rows)
            )
            or "Ma'lumot yo'q"
        )
        await show(cb, text, kb(back("stats")))
        return
    if act == "custom":
        await state.set_state(St.stats_from)
        await show(cb, "📅 Boshlanish sanasi (YYYY-MM-DD):", kb(back("stats")))
        return
    await screen_stats(cb, svc, period)


@router.message(St.stats_from, F.text)
async def stats_from(m: Message, state: FSMContext) -> None:
    from datetime import date

    try:
        d = date.fromisoformat((m.text or "").strip())
    except ValueError:
        await m.answer("Format: YYYY-MM-DD")
        return
    await state.update_data(frm=d.isoformat())
    await state.set_state(St.stats_to)
    await m.answer("📅 Tugash sanasi (YYYY-MM-DD):")


@router.message(St.stats_to, F.text)
async def stats_to(m: Message, state: FSMContext, svc: Services) -> None:
    from datetime import date

    try:
        to = date.fromisoformat((m.text or "").strip())
        frm = date.fromisoformat((await state.get_data())["frm"])
        p = resolve_period("custom", frm, to)
    except (ValueError, KeyError):
        await m.answer("Noto'g'ri davr. Qaytadan: /admin")
        return
    await state.clear()
    a = AnalyticsService(svc.session)
    await m.answer(format_stats(f"Davr {frm} – {to}", await a.dashboard(p), None), reply_markup=kb(BACK))


# ---------------- orders ----------------
FILTERS = [
    ("review", "🔍 Tekshirish"),
    ("failed", "❌ Xato"),
    ("processing", "⚙️ Jarayonda"),
    ("awaiting_payment", "⏳ Kutilmoqda"),
    ("completed", "✅ Bajarilgan"),
]


async def sec_orders(
    cb: CallbackQuery,
    svc: Services,
    role: AdminRole,
    user: User,
    state: FSMContext,
    rt: Runtime,
    act: str,
    id_: str,
    page: int,
) -> None:
    if act == "view":
        await screen_order(cb, svc, role, id_)
    elif act == "list":
        await screen_orders(cb, svc, id_, page)
    elif act == "find":
        await state.set_state(St.find_order)
        await show(cb, "🔎 Buyurtma ID (PR-XXXXXX), @username yoki user ID yuboring:", kb(back("orders")))
    elif act in ("retry", "refund", "complete"):
        if act != "retry" and not await need(cb, role, AdminRole.ADMIN):
            return
        label = {
            "retry": "🔄 Qayta urinish",
            "refund": "↩️ Pulni qaytarish",
            "complete": "✅ Qo'lda bajarildi deb belgilash",
        }[act]
        await ask_confirm(
            cb, f"{label}: <code>{id_}</code>", f"order_{act}", {"id": id_}, user.id, danger=act == "refund"
        )
    else:
        review = (
            await svc.session.scalar(
                select(func.count()).select_from(Order).where(Order.status == OrderStatus.NEEDS_REVIEW)
            )
        ) or 0
        rows = [
            btn(f"{label}{f' ({review})' if key == 'review' and review else ''}", Adm(sec="orders", act="list", id=key))
            for key, label in FILTERS
        ]
        await show(
            cb,
            "📦 <b>Buyurtmalar</b>",
            kb(rows[:2], rows[2:4], rows[4:], btn("🔎 Qidirish", Adm(sec="orders", act="find")), BACK),
        )


async def screen_orders(
    ev: Message | CallbackQuery, svc: Services, key: str, page: int, orders: list[Order] | None = None
) -> None:
    per = 8
    if orders is None:
        stmt = select(Order).order_by(Order.id.desc()).limit(per + 1).offset(page * per)
        if key == "review":
            stmt = stmt.where(Order.status == OrderStatus.NEEDS_REVIEW)
        elif key in {s.value for s in OrderStatus}:
            stmt = stmt.where(Order.status == OrderStatus(key))
        orders = list((await svc.session.scalars(stmt)).all())
    items = [
        btn(
            f"🔍 {o.public_id} · {o.plan_months or o.stars_amount}{'м' if o.plan_months else '⭐'} · {o.price_usd:.2f}$ · {o.status.value}",
            Adm(sec="orders", act="view", id=o.public_id),
        )
        for o in orders[:per]
    ]
    nav = []
    if page > 0:
        nav.append(btn("◀️", Adm(sec="orders", act="list", id=key, page=page - 1)))
    if len(orders) > per:
        nav.append(btn("▶️", Adm(sec="orders", act="list", id=key, page=page + 1)))
    await show(ev, f"📦 <b>Buyurtmalar</b> · {key}" + ("" if items else "\n\nBo'sh."), kb(*items, nav, back("orders")))


async def screen_order(ev: Message | CallbackQuery, svc: Services, role: AdminRole, public_id: str) -> None:
    try:
        o = await OrderService(svc.session).by_public_id(public_id)
    except AppError:
        await show(ev, "❌ Buyurtma topilmadi", kb(back("orders")))
        return
    u = await svc.session.get(User, o.user_id)
    events = " → ".join(e.to_status.value for e in await OrderService(svc.session).events(o.id))
    lines = [
        f"🧾 <b>{o.public_id}</b> · {o.status.value}",
        f"👤 Xaridor: {u.first_name if u else ''} (@{u.username if u else '-'} · <code>{o.user_id}</code>)",
        f"{'💎 Premium ' + str(o.plan_months) + ' oy' if o.plan_months else '⭐ Stars ' + str(o.stars_amount)} → {('@' + o.recipient_username) if o.recipient_username else o.recipient_user_id}",
        f"💵 {o.price_usd:.2f} $ · {o.price_amount.normalize() if o.price_amount else '-'} {o.price_currency or ''} · {o.payment_method.value}",
        f"🔧 Provider: {o.provider.value if o.provider else '—'} · urinish {o.attempts}",
    ]
    if o.cost_usd is not None:
        lines.append(f"📉 Tannarx {o.cost_usd:.2f} $ · foyda {o.profit_usd:.2f} $")
    if o.error_code:
        lines.append(f"❗️ Xato: {o.error_code} {o.error_message or ''}")
    lines.append(f"📜 {events}")
    rows: list[Any] = []
    if o.status in (OrderStatus.NEEDS_REVIEW, OrderStatus.FAILED):
        rows.append(
            [btn("✅ Bajarildi deb belgilash", Adm(sec="orders", act="complete", id=o.public_id), style="success")]
            if has(role, AdminRole.ADMIN)
            else []
        )
        rows.append([btn("🔄 Qayta urinish", Adm(sec="orders", act="retry", id=o.public_id), style="primary")])
    if o.status in (OrderStatus.NEEDS_REVIEW, OrderStatus.FAILED, OrderStatus.PAID) and has(role, AdminRole.ADMIN):
        rows.append([btn("↩️ Pulni qaytarish", Adm(sec="orders", act="refund", id=o.public_id), style="danger")])
    rows.append([btn("👤 Xaridor", Adm(sec="users", act="view", id=str(o.user_id)))])
    if o.provider_ref and len(o.provider_ref) == 64:
        rows.append([btn("🔗 Tonviewer", url=f"https://tonviewer.com/transaction/{o.provider_ref}")])
    rows.append([back("orders")])
    await show(ev, "\n".join(lines), kb(*rows))


@router.message(St.find_order, F.text)
async def find_order(m: Message, svc: Services, state: FSMContext, role: AdminRole) -> None:
    await state.clear()
    q = (m.text or "").strip().lstrip("@")
    stmt = (
        select(Order)
        .where(
            (Order.public_id == q.upper())
            | (func.lower(Order.recipient_username) == q.lower())
            | (Order.user_id == (int(q) if q.isdigit() else -1))
        )
        .order_by(Order.id.desc())
        .limit(9)
    )
    found = list((await svc.session.scalars(stmt)).all())
    if len(found) == 1:
        await screen_order(m, svc, role, found[0].public_id)
    else:
        await screen_orders(m, svc, "search", 0, found)


# ---------------- users ----------------
async def sec_users(
    cb: CallbackQuery,
    svc: Services,
    role: AdminRole,
    user: User,
    state: FSMContext,
    rt: Runtime,
    act: str,
    id_: str,
    page: int,
) -> None:
    if act == "view":
        await screen_user(cb, svc, role, int(id_))
    elif act in ("new", "top", "banned"):
        stmt = select(User)
        stmt = {
            "new": stmt.order_by(User.created_at.desc()),
            "top": stmt.order_by(User.total_spent_usd.desc()),
            "banned": stmt.where(User.is_banned.is_(True)),
        }[act]
        rows = (await svc.session.scalars(stmt.limit(10))).all()
        await show(
            cb,
            "👥 Foydalanuvchilar",
            kb(
                *[
                    btn(
                        f"{u.first_name or ''} @{u.username or '-'} · {u.total_spent_usd:.0f}$",
                        Adm(sec="users", act="view", id=str(u.id)),
                    )
                    for u in rows
                ],
                back("users"),
            ),
        )
    elif act == "search":
        await state.set_state(St.user_search)
        await show(cb, "🔍 ID, @username yoki ism yuboring:", kb(back("users")))
    elif act in ("credit", "debit"):
        if not await need(cb, role, AdminRole.ADMIN):
            return
        await state.update_data(uid=int(id_), sign=1 if act == "credit" else -1)
        await state.set_state(St.balance_amount)
        await show(
            cb,
            f"{'➕' if act == 'credit' else '➖'} Summani yuboring (USD), ixtiyoriy izoh bilan: <code>5 sovg'a</code>",
            kb(btn("✖️ Bekor", Adm(sec="users", act="view", id=id_), style="danger")),
        )
    elif act == "msg":
        await state.update_data(uid=int(id_))
        await state.set_state(St.message_text)
        await show(
            cb, "✉️ Xabar matnini yuboring:", kb(btn("✖️ Bekor", Adm(sec="users", act="view", id=id_), style="danger"))
        )
    elif act in ("ban", "unban"):
        if not await need(cb, role, AdminRole.ADMIN):
            return
        await ask_confirm(
            cb,
            f"{'⛔️ Bloklash' if act == 'ban' else '✅ Blokdan chiqarish'}: <code>{id_}</code>",
            act,
            {"user_id": int(id_)},
            user.id,
            danger=act == "ban",
        )
    elif act == "ledger":
        txs = await BalanceService(svc.session).history(int(id_), 10)
        text = "📜 <b>Balans tarixi</b>\n\n" + (
            "\n".join(f"{t.amount_usd:+.2f} $ · {t.type.value} · {dt(t.created_at)}" for t in txs) or "Bo'sh"
        )
        await show(cb, text, kb(btn("« Orqaga", Adm(sec="users", act="view", id=id_))))
    elif act == "orders":
        orders = await OrderService(svc.session).list_for_user(int(id_), None, 8, 0)
        await screen_orders(cb, svc, "search", 0, orders)
    else:
        await show(
            cb,
            "👥 <b>Foydalanuvchilar</b>",
            kb(
                btn("🔍 Qidirish", Adm(sec="users", act="search")),
                [
                    btn("🆕 Yangilar", Adm(sec="users", act="new")),
                    btn("💰 Top xaridorlar", Adm(sec="users", act="top")),
                ],
                btn("⛔️ Bloklanganlar", Adm(sec="users", act="banned")),
                BACK,
            ),
        )


async def screen_user(ev: Message | CallbackQuery, svc: Services, role: AdminRole, uid: int) -> None:
    try:
        u = await UserService(svc.session).get(uid)
    except AppError:
        await show(ev, "❌ Topilmadi", kb(back("users")))
        return
    invited = (await svc.session.scalar(select(func.count()).select_from(User).where(User.referrer_id == uid))) or 0
    text = (
        f"👤 <b>{u.first_name or ''} {u.last_name or ''}</b> (@{u.username or '-'})\n🆔 <code>{u.id}</code> · {u.language} · TG Premium: {'ha' if u.tg_is_premium else 'yo`q'}\n"
        f"📅 Ro'yxat: {dt(u.created_at)} · Oxirgi faollik: {dt(u.last_seen_at)}\n💼 Balans: {u.balance_usd:.2f} $\n📦 Buyurtmalar: {u.orders_count} · Jami xarid: {u.total_spent_usd:.2f} $\n"
        f"👥 Taklif qilgan: {invited} · Taklif qilgan odam: {u.referrer_id or '—'}\nManba: {u.source or '—'} · Holat: {'⛔️ bloklangan' if u.is_banned else '✅ faol'}"
    )
    rows: list[Any] = []
    if has(role, AdminRole.ADMIN):
        rows.append(
            [
                btn("➕ Balans qo'shish", Adm(sec="users", act="credit", id=str(uid)), style="success"),
                btn("➖ Balans ayirish", Adm(sec="users", act="debit", id=str(uid)), style="danger"),
            ]
        )
    rows.append(
        [
            btn("✉️ Xabar yozish", Adm(sec="users", act="msg", id=str(uid)), style="primary"),
            btn("📦 Buyurtmalari", Adm(sec="users", act="orders", id=str(uid))),
        ]
    )
    if has(role, AdminRole.ADMIN):
        rows.append(
            [
                btn("✅ Blokdan chiqarish", Adm(sec="users", act="unban", id=str(uid)), style="success")
                if u.is_banned
                else btn("⛔️ Bloklash", Adm(sec="users", act="ban", id=str(uid)), style="danger")
            ]
        )
    rows.append([btn("📜 Balans tarixi", Adm(sec="users", act="ledger", id=str(uid))), back("users")])
    await show(ev, text, kb(*rows))


async def user_search_results(m: Message, svc: Services, q: str) -> None:
    found = await UserService(svc.session).search(q, 8)
    if not found:
        await m.answer("❌ Topilmadi", reply_markup=kb(back("users")))
        return
    await m.answer(
        "🔍 Natijalar:",
        reply_markup=kb(
            *[
                btn(f"{u.first_name or ''} @{u.username or '-'} · {u.id}", Adm(sec="users", act="view", id=str(u.id)))
                for u in found
            ],
            back("users"),
        ),
    )


@router.message(St.user_search, F.text)
async def on_user_search(m: Message, svc: Services, state: FSMContext) -> None:
    await state.clear()
    await user_search_results(m, svc, m.text or "")


@router.message(St.balance_amount, F.text)
async def on_balance_amount(m: Message, state: FSMContext, user: User) -> None:
    data = await state.get_data()
    parts = (m.text or "").split(maxsplit=1)
    try:
        amount = D(parts[0].replace(",", ".")) * data["sign"]
    except (InvalidOperation, IndexError, TypeError):
        await m.answer("❌ Summa noto'g'ri. Masalan: <code>5 sovg'a</code>")
        return
    await state.clear()
    await ask_confirm(
        m,
        f"💼 <code>{data['uid']}</code> balansiga <b>{amount:+.2f} $</b>",
        "balance",
        {"user_id": data["uid"], "amount": str(amount), "comment": parts[1] if len(parts) > 1 else None},
        user.id,
        danger=amount < 0,
    )


@router.message(St.message_text, F.text)
async def on_message_user(m: Message, svc: Services, state: FSMContext) -> None:
    uid = (await state.get_data())["uid"]
    await state.clear()
    target = await UserService(svc.session).get(uid)
    await svc.notifier.notify_user(target, "admin_message", text=m.html_text)
    await m.answer("✅ Yuborildi", reply_markup=kb(btn("« Foydalanuvchi", Adm(sec="users", act="view", id=str(uid)))))


# ---------------- finance ----------------
async def screen_fin(ev: Message | CallbackQuery, svc: Services, role: AdminRole) -> None:
    s = get_settings()
    lines = ["💰 <b>Moliya</b>\n━━━━━━━━━━━━━━━━"]
    addr = await svc.settings.get("hot_wallet.address")
    if addr:
        try:
            hw = svc.hot_wallet()
            bal, wd = await hw.balance(), await hw.withdrawable()
            rate = await svc.rates.ton_usd()
            lines.append(
                f"💎 Hot wallet: {bal:.2f} TON (≈ {bal * rate:.2f} $)\n   Rezerv: {await svc.settings.get('hot_wallet.reserve_ton')} TON · Yechish mumkin: {wd:.2f} TON"
            )
        except Exception as exc:  # noqa: BLE001
            lines.append(f"💎 Hot wallet: xato ({str(exc)[:50]})")
    else:
        lines.append("💎 Hot wallet: sozlanmagan (<code>python -m app.cli wallet generate</code>)")
    stars_in = (
        await svc.session.scalar(
            select(func.coalesce(func.sum(StarsTransaction.amount), 0)).where(StarsTransaction.direction == "in")
        )
    ) or 0
    stars_out = (
        await svc.session.scalar(
            select(func.coalesce(func.sum(StarsTransaction.amount), 0)).where(StarsTransaction.direction == "out")
        )
    ) or 0
    lines.append(f"⭐ Stars (ledger): {stars_in - stars_out} ⭐")
    liab = (await svc.session.scalar(select(func.coalesce(func.sum(User.balance_usd), 0)))) or 0
    lines.append(f"💼 Foydalanuvchi balanslari: {D(liab):.2f} $")
    lines.append(
        f"━━━━━━━━━━━━━━━━\n🏦 Admin hamyon: <code>{s.admin_ton_address or '—'}</code>\n🔁 Avto-o'tkazish: {'✅' if await svc.settings.get('hot_wallet.sweep_enabled') else '⛔️'}"
    )
    unmatched = (
        await svc.session.scalar(
            select(func.count()).select_from(UnmatchedTonTx).where(UnmatchedTonTx.resolution == "pending")
        )
    ) or 0
    rows: list[Any] = []
    if role == AdminRole.OWNER:
        rows.append(btn("💸 Telegram Wallet'ga yechish", Adm(sec="fin", act="withdraw"), style="success"))
        rows.append(
            btn(
                f"🔁 Avto-o'tkazish: {'o`chirish' if await svc.settings.get('hot_wallet.sweep_enabled') else 'yoqish'}",
                Adm(sec="fin", act="sweep"),
            )
        )
    rows += [
        [btn("🧾 Xarajatlar", Adm(sec="fin", act="expenses")), btn("➕ Xarajat", Adm(sec="fin", act="addexp"))],
        [
            btn("📜 Hot wallet tarixi", Adm(sec="fin", act="hwtx")),
            btn(f"❓ Mos kelmaganlar ({unmatched})", Adm(sec="fin", act="unmatched")),
        ],
        btn("⭐ Stars'ni qanday yechish?", Adm(sec="fin", act="starshelp")),
        BACK,
    ]
    await show(ev, "\n".join(lines), kb(*rows))


async def withdraw_confirm(ev: Message | CallbackQuery, svc: Services, user: User, raw: str) -> None:
    try:
        amount = D(raw.replace(",", "."))
    except InvalidOperation:
        await show(ev, "❌ Summa noto'g'ri", kb(back("fin")))
        return
    addr = get_settings().admin_ton_address
    await ask_confirm(
        ev,
        f"💸 <b>{amount} TON</b> → <code>{addr}</code> (.env dagi admin manzil)",
        "withdraw",
        {"amount": str(amount)},
        user.id,
        danger=False,
    )


async def sec_fin(
    cb: CallbackQuery,
    svc: Services,
    role: AdminRole,
    user: User,
    state: FSMContext,
    rt: Runtime,
    act: str,
    id_: str,
    page: int,
) -> None:
    if act in ("withdraw", "sweep") and not await need(cb, role, AdminRole.OWNER):
        return
    if act == "withdraw":
        await state.set_state(St.withdraw_amount)
        wd = await svc.hot_wallet().withdrawable()
        await show(cb, f"💸 Qancha TON yechasiz? (maksimal {wd:.2f})", kb(back("fin", "✖️ Bekor")))
    elif act == "sweep":
        await ask_confirm(cb, "🔁 Avto-o'tkazishni almashtirish", "sweep_toggle", {}, user.id, danger=False)
    elif act == "addexp":
        await state.set_state(St.expense_amount)
        await show(cb, "➕ Xarajat summasi (USD):", kb(back("fin", "✖️ Bekor")))
    elif act == "cat":
        await state.update_data(category=id_)
        await state.set_state(St.expense_note)
        await show(cb, "📝 Izoh yuboring (yoki <code>-</code>):", kb(back("fin", "✖️ Bekor")))
    elif act == "expenses":
        from app.models import Expense

        exps = (await svc.session.scalars(select(Expense).order_by(Expense.id.desc()).limit(10))).all()
        await show(
            cb,
            "🧾 <b>So'nggi xarajatlar</b>\n\n"
            + (
                "\n".join(
                    f"{e.spent_on:%d.%m} · {e.category.value} · {e.amount_usd:.2f} $ {e.note or ''}" for e in exps
                )
                or "Bo'sh"
            ),
            kb(back("fin")),
        )
    elif act == "hwtx":
        from app.models import HotWalletTransaction as H

        hwrows = (await svc.session.scalars(select(H).order_by(H.id.desc()).limit(10))).all()
        await show(
            cb,
            "📜 <b>Hot wallet</b>\n\n"
            + (
                "\n".join(
                    f"{'⬇️' if r.direction.value == 'in' else '⬆️'} {r.amount_ton:.2f} TON · {r.kind.value} · {dt(r.created_at)}"
                    for r in hwrows
                )
                or "Bo'sh"
            ),
            kb(back("fin")),
        )
    elif act == "unmatched":
        ums = (
            await svc.session.scalars(select(UnmatchedTonTx).where(UnmatchedTonTx.resolution == "pending").limit(10))
        ).all()
        items = [
            btn(f"{r.amount_ton:.2f} TON · {r.comment or '-'}", Adm(sec="fin", act="um", id=str(r.id))) for r in ums
        ]
        await show(
            cb,
            "❓ <b>Mos kelmagan to'lovlar</b>\nBirini tanlang va foydalanuvchiga biriktiring.",
            kb(*items, back("fin")),
        )
    elif act == "um":
        await state.update_data(um=int(id_))
        await state.set_state(St.admin_user)
        await state.update_data(mode="unmatched")
        await show(
            cb,
            "Foydalanuvchi ID'sini yuboring (balansga yoziladi) yoki <code>ignore</code>:",
            kb(back("fin", "✖️ Bekor")),
        )
    elif act == "starshelp":
        await show(
            cb,
            "⭐ <b>Stars'ni yechish</b>\n1. @BotFather → botingiz → Bot Settings → Balance\n2. «Withdraw» (kamida 1000 ⭐, 21 kun o'tgan Stars)\n3. Fragment orqali TON olinadi va Telegram Wallet'ingizga tushadi.\nBu jarayonni API orqali avtomatlashtirib bo'lmaydi.",
            kb(back("fin")),
        )
    else:
        await screen_fin(cb, svc, role)


@router.message(St.withdraw_amount, F.text)
async def on_withdraw_amount(m: Message, svc: Services, state: FSMContext, user: User, role: AdminRole) -> None:
    if not await need(m, role, AdminRole.OWNER):
        return
    await state.clear()
    await withdraw_confirm(m, svc, user, m.text or "")


@router.message(St.expense_amount, F.text)
async def on_expense_amount(m: Message, state: FSMContext) -> None:
    try:
        amount = D((m.text or "").replace(",", "."))
        assert amount > 0
    except (InvalidOperation, AssertionError):
        await m.answer("❌ Summa noto'g'ri")
        return
    await state.update_data(amount=str(amount))
    await state.set_state(None)
    cats = [btn(c.value, Adm(sec="fin", act="cat", id=c.value)) for c in ExpenseCategory]
    await m.answer("Kategoriyani tanlang:", reply_markup=kb(cats[:3], cats[3:6], cats[6:], back("fin", "✖️ Bekor")))


@router.message(St.expense_note, F.text)
async def on_expense_note(m: Message, svc: Services, state: FSMContext, user: User, role: AdminRole) -> None:
    data = await state.get_data()
    await state.clear()
    note = None if (m.text or "").strip() == "-" else (m.text or "")[:200]
    await AdminService(svc.session, svc.settings).add_expense(
        user.id, ExpenseCategory(data["category"]), D(data["amount"]), note
    )
    await m.answer("✅ Xarajat saqlandi", reply_markup=kb(back("fin")))


# ---------------- pricing ----------------
async def screen_price(ev: Message | CallbackQuery, svc: Services) -> None:
    ton, uzs_rate = await svc.rates.ton_usd(), await svc.rates.usd_uzs()
    lines = [
        f"🏷 <b>Narxlar</b> (1 TON = {ton:.2f} $ · 1 $ = {int(uzs_rate):,} so'm)\n━━━━━━━━━━━━━━━━".replace(",", " ")
    ]
    rows: list[Any] = []
    for p in (await svc.session.scalars(select(PremiumPlan).order_by(PremiumPlan.sort_order))).all():
        if not p.provider_supported:
            lines.append(f"💎 {p.months} oy ⛔️ Telegram qo'llamaydi")
        else:
            try:
                q = await svc.pricing.quote_premium(p)
                lines.append(
                    f"💎 {p.months} oy {'✅' if p.is_enabled else '⛔️'} tannarx {q.cost_usd:.2f} → <b>{q.price_usd:.2f} $</b> (foyda {q.price_usd - q.cost_usd:.2f}) · {p.price_stars} ⭐"
                )
            except AppError:
                lines.append(f"💎 {p.months} oy {'✅' if p.is_enabled else '⛔️'} narx noma'lum (tannarx kiritilmagan)")
        rows.append(btn(f"💎 {p.months} oy", Adm(sec="price", act="plan", id=str(p.id))))
    lines.append(
        f"⭐ Stars: ustama {await svc.settings.get('pricing.stars.markup_percent')}% · min foyda {await svc.settings.get('pricing.min_margin_percent')}%"
    )
    await show(
        ev,
        "\n".join(lines),
        kb(
            rows[:2],
            rows[2:],
            btn("⭐ Stars ustamasi", Adm(sec="price", act="smarkup")),
            btn("🔄 Fragment narxini yangilash", Adm(sec="price", act="refresh"), style="primary"),
            BACK,
        ),
    )


async def sec_price(
    cb: CallbackQuery,
    svc: Services,
    role: AdminRole,
    user: User,
    state: FSMContext,
    rt: Runtime,
    act: str,
    id_: str,
    page: int,
) -> None:
    if act == "plan":
        p = await svc.session.get(PremiumPlan, int(id_))
        assert p is not None
        text = f"💎 <b>{p.months} oy</b>\nUstama: {p.markup_percent}% (+{p.fixed_markup_usd}$)\nQat'iy narx: {p.fixed_price_usd or '—'}\nStars narxi: {p.price_stars}\nTannarx (TON): {p.cost_ton or '—'}\nBelgi: {p.badge or '—'}"
        rows = [
            [
                btn("✏️ Ustama %", Adm(sec="price", act="e_markup_percent", id=id_)),
                btn("✏️ Qat'iy narx", Adm(sec="price", act="e_fixed_price_usd", id=id_)),
            ],
            [
                btn("✏️ Stars narxi", Adm(sec="price", act="e_price_stars", id=id_)),
                btn("✏️ Belgi", Adm(sec="price", act="e_badge", id=id_)),
            ],
            [
                btn("✏️ Telegram narxi (taqqoslash)", Adm(sec="price", act="e_reference_price_usd", id=id_)),
                btn("✏️ Tannarx (TON)", Adm(sec="price", act="e_cost_ton", id=id_)),
            ],
            [
                btn("⛔️ O'chirish", Adm(sec="price", act="toggle", id=id_), style="danger")
                if p.is_enabled
                else btn("✅ Yoqish", Adm(sec="price", act="toggle", id=id_), style="success")
            ],
            [back("price")],
        ]
        await show(cb, text, kb(*rows))
    elif act.startswith("e_"):
        await state.update_data(plan_id=int(id_), field=act[2:])
        await state.set_state(St.plan_value)
        await show(
            cb,
            "Yangi qiymatni yuboring (o'chirish uchun <code>-</code>):",
            kb(btn("✖️ Bekor", Adm(sec="price", act="plan", id=id_), style="danger")),
        )
    elif act == "toggle":
        p = await svc.session.get(PremiumPlan, int(id_))
        assert p is not None
        try:
            await AdminService(svc.session, svc.settings).update_plan(user.id, p.id, is_enabled=not p.is_enabled)
        except AppError as exc:
            await toast(cb, exc.message, alert=True)
            return
        await sec_price(cb, svc, role, user, state, rt, "plan", id_, 0)
    elif act == "smarkup":
        await state.set_state(St.stars_markup)
        await show(cb, "⭐ Stars ustamasi (%) ni yuboring:", kb(back("price", "✖️ Bekor")))
    elif act == "refresh":
        from app.api.runtime import build_providers

        n = await AdminService(svc.session, svc.settings).refresh_provider_prices(
            list((await build_providers(svc.settings, rt)).values())
        )
        await toast(cb, f"🔄 Yangilandi: {n}", alert=True)
        await screen_price(cb, svc)
    else:
        await screen_price(cb, svc)


@router.message(St.plan_value, F.text)
async def on_plan_value(m: Message, svc: Services, state: FSMContext, user: User) -> None:
    data = await state.get_data()
    await state.clear()
    raw = (m.text or "").strip()
    field = data["field"]
    value: Any = None
    if raw != "-":
        try:
            value = raw if field == "badge" else int(raw) if field == "price_stars" else D(raw.replace(",", "."))
        except (ValueError, InvalidOperation):
            await m.answer("❌ Qiymat noto'g'ri", reply_markup=kb(back("price")))
            return
    try:
        await AdminService(svc.session, svc.settings).update_plan(user.id, data["plan_id"], **{field: value})
    except AppError as exc:
        await m.answer(f"❌ {exc.message}", reply_markup=kb(back("price")))
        return
    await m.answer("✅ Saqlandi", reply_markup=kb(btn("« Narxlar", Adm(sec="price"))))


@router.message(St.stars_markup, F.text)
async def on_stars_markup(m: Message, svc: Services, state: FSMContext, user: User) -> None:
    await state.clear()
    try:
        v = D((m.text or "").replace(",", ".").replace("%", ""))
        assert 0 <= v <= 100
    except (InvalidOperation, AssertionError):
        await m.answer("❌ 0–100 oralig'ida son yuboring", reply_markup=kb(back("price")))
        return
    await svc.settings.set("pricing.stars.markup_percent", str(v), user.id)
    await AdminService(svc.session, svc.settings).audit.log(
        user.id, "price.stars_markup", "settings", None, None, str(v)
    )
    await m.answer("✅ Saqlandi", reply_markup=kb(btn("« Narxlar", Adm(sec="price"))))


# ---------------- payment methods ----------------
METHOD_KEYS = [
    ("payments.ton.enabled", "💎 TON"),
    ("payments.stars.enabled", "⭐ Stars"),
    ("payments.balance.enabled", "💼 Balans"),
    ("payments.topup.stars.enabled", "➕ Stars bilan balans to'ldirish"),
]


async def sec_methods(
    cb: CallbackQuery,
    svc: Services,
    role: AdminRole,
    user: User,
    state: FSMContext,
    rt: Runtime,
    act: str,
    id_: str,
    page: int,
) -> None:
    if act == "toggle" and id_ in dict(METHOD_KEYS):
        await svc.settings.set(id_, not await svc.settings.get(id_), user.id)
        await AdminService(svc.session, svc.settings).audit.log(user.id, "settings.update", "setting", id_)
    rows = []
    lines = ["💳 <b>To'lov usullari</b>"]
    for key, label in METHOD_KEYS:
        on = bool(await svc.settings.get(key))
        lines.append(f"{label} — {'✅ yoqilgan' if on else '⛔️ o`chirilgan'}")
        rows.append(
            btn(
                f"{'✅' if on else '⛔️'} {label}",
                Adm(sec="methods", act="toggle", id=key),
                style="success" if on else None,
            )
        )
    lines.append(f"⏱ Invoice muddati: {await svc.settings.get('payments.invoice_ttl_minutes')} daqiqa")
    await show(cb, "\n".join(lines), kb(*rows, BACK))


# ---------------- referral ----------------
async def sec_ref(
    cb: CallbackQuery,
    svc: Services,
    role: AdminRole,
    user: User,
    state: FSMContext,
    rt: Runtime,
    act: str,
    id_: str,
    page: int,
) -> None:
    if act == "toggle":
        await svc.settings.set("referral.enabled", not await svc.settings.get("referral.enabled"), user.id)
    elif act == "percent":
        await state.update_data(setting="referral.percent")
        await state.set_state(St.setting_value)
        await show(cb, "Foizni yuboring (masalan 2):", kb(back("ref", "✖️ Bekor")))
        return
    elif act == "top":
        rows = await AnalyticsService(svc.session).top_referrers()
        await show(
            cb,
            "🏆 <b>Top referallar</b>\n\n"
            + (
                "\n".join(
                    f"{i + 1}. <code>{r['id']}</code> — {r['earned_usd']} $ ({r['rewards']})"
                    for i, r in enumerate(rows)
                )
                or "Bo'sh"
            ),
            kb(back("ref")),
        )
        return
    on = bool(await svc.settings.get("referral.enabled"))
    await show(
        cb,
        f"🤝 <b>Referal tizimi</b>\nHolat: {'✅ yoqilgan' if on else '⛔️ o`chiq'}\nBonus: {await svc.settings.get('referral.percent')}%",
        kb(
            btn(
                "⛔️ O'chirish" if on else "✅ Yoqish", Adm(sec="ref", act="toggle"), style="danger" if on else "success"
            ),
            [
                btn(f"✏️ Foiz: {await svc.settings.get('referral.percent')}%", Adm(sec="ref", act="percent")),
                btn("🏆 Top referallar", Adm(sec="ref", act="top")),
            ],
            BACK,
        ),
    )


# ---------------- generic settings ----------------
NUMERIC_SETTINGS = {
    "referral.percent",
    "pricing.min_margin_percent",
    "pricing.network_fee_ton",
    "payments.invoice_ttl_minutes",
    "hot_wallet.reserve_ton",
    "hot_wallet.daily_withdraw_limit_ton",
}


async def sec_set(
    cb: CallbackQuery,
    svc: Services,
    role: AdminRole,
    user: User,
    state: FSMContext,
    rt: Runtime,
    act: str,
    id_: str,
    page: int,
) -> None:
    if act == "maint":
        await ask_confirm(cb, "🛠 Texnik ishlar rejimini almashtirish", "maint_toggle", {}, user.id, danger=False)
        return
    if act == "health":
        await show(cb, await health_text(svc, rt), kb(btn("🔄 Yangilash", Adm(sec="set", act="health")), back("set")))
        return
    if act == "events":
        events = dict(await svc.settings.get("notify.events") or {})
        if id_ in events:
            events[id_] = not events[id_]
            await svc.settings.set("notify.events", events, user.id)
        events = dict(await svc.settings.get("notify.events") or {})
        await show(
            cb,
            "🔔 <b>Log kanal bildirishnomalari</b>",
            kb(
                *[btn(f"{'✅' if v else '⛔️'} {k}", Adm(sec="set", act="events", id=k)) for k, v in events.items()],
                back("set"),
            ),
        )
        return
    if act in ("support", "logchat", "min_margin", "fee", "ttl", "reserve", "welcome"):
        keys = {
            "support": "bot.support_username",
            "logchat": "notify.log_chat_id",
            "min_margin": "pricing.min_margin_percent",
            "fee": "pricing.network_fee_ton",
            "ttl": "payments.invoice_ttl_minutes",
            "reserve": "hot_wallet.reserve_ton",
        }
        await state.update_data(setting=keys[act])
        await state.set_state(St.setting_value)
        await show(cb, f"✏️ Yangi qiymatni yuboring (<code>{keys[act]}</code>):", kb(back("set", "✖️ Bekor")))
        return
    if act == "fragment":
        if role != AdminRole.OWNER:
            await toast(cb, "Faqat owner", alert=True)
            return
        has_cookie = bool(await svc.settings.get("fragment.cookies"))
        await show(
            cb,
            f"🔐 <b>Fragment</b>\nRejim: {await svc.settings.get('fragment.mode')}\nCookie: {'✅ kiritilgan' if has_cookie else '— yo`q'}",
            kb(btn("🔑 Cookie yangilash", Adm(sec="set", act="cookie"), style="success"), back("set")),
        )
        return
    if act == "cookie":
        await state.set_state(St.fragment_cookies)
        await show(
            cb,
            "🔑 Cookie'larni bitta xabarda yuboring:\n<code>stel_ssid=...; stel_dt=...; stel_token=...; stel_ton_token=...</code>\nXabar o'qilgach darhol o'chiriladi.",
            kb(back("set", "✖️ Bekor")),
        )
        return
    maint = bool(await svc.settings.get("bot.maintenance"))
    text = f"⚙️ <b>Sozlamalar</b>\nSupport: @{await svc.settings.get('bot.support_username') or '—'}\nLog chat: <code>{await svc.settings.get('notify.log_chat_id') or '—'}</code>\nMin foyda: {await svc.settings.get('pricing.min_margin_percent')}% · Tarmoq fee: {await svc.settings.get('pricing.network_fee_ton')} TON\nTexnik ishlar: {'🛠 YOQILGAN' if maint else 'o`chiq'}"
    await show(cb, text, kb(
        [btn("🆘 Support username", Adm(sec="set", act="support")), btn("📮 Log chat ID", Adm(sec="set", act="logchat"))],
        [btn("✏️ Min foyda %", Adm(sec="set", act="min_margin")), btn("✏️ Tarmoq fee", Adm(sec="set", act="fee"))],
        [btn("⏱ Invoice muddati", Adm(sec="set", act="ttl")), btn("🛡 Hot wallet rezerv", Adm(sec="set", act="reserve"))],
        [btn("🔔 Bildirishnomalar", Adm(sec="set", act="events")), btn("🔐 Fragment", Adm(sec="set", act="fragment"))],
        btn("🛠 Texnik ishlar: " + ("o'chirish" if maint else "yoqish"), Adm(sec="set", act="maint"), style="danger"),
        [btn("🩺 Tizim holati", Adm(sec="set", act="health"))],
        BACK,
    ))  # fmt: skip


@router.message(St.setting_value, F.text)
async def on_setting_value(m: Message, svc: Services, state: FSMContext, user: User) -> None:
    key = (await state.get_data())["setting"]
    await state.clear()
    raw = (m.text or "").strip()
    try:
        value: Any
        if key == "bot.support_username":
            value = raw.lstrip("@")
        elif key == "notify.log_chat_id":
            value = int(raw)
        elif key == "payments.invoice_ttl_minutes":
            value = int(raw)
            assert 5 <= value <= 120
        else:
            value = str(D(raw.replace(",", ".")))
    except (ValueError, InvalidOperation, AssertionError):
        await m.answer("❌ Qiymat noto'g'ri", reply_markup=kb(BACK))
        return
    before = await svc.settings.get(key)
    await svc.settings.set(key, value, user.id)
    await AdminService(svc.session, svc.settings).audit.log(user.id, "settings.update", "setting", key, before, value)
    await m.answer("✅ Saqlandi", reply_markup=kb(BACK))


@router.message(St.fragment_cookies, F.text)
async def on_cookies(m: Message, svc: Services, state: FSMContext, user: User, role: AdminRole) -> None:
    await state.clear()
    if role != AdminRole.OWNER:
        return
    try:
        await m.delete()
    except Exception:  # noqa: BLE001
        pass
    await svc.settings.set("fragment.cookies", (m.text or "").strip(), user.id)
    await AdminService(svc.session, svc.settings).audit.log(
        user.id, "settings.fragment_cookies", "setting", "fragment.cookies"
    )
    await m.answer("✅ Cookie saqlandi (shifrlangan). Xabaringiz o'chirildi.", reply_markup=kb(BACK))


# ---------------- promo ----------------
async def sec_promo(
    cb: CallbackQuery,
    svc: Services,
    role: AdminRole,
    user: User,
    state: FSMContext,
    rt: Runtime,
    act: str,
    id_: str,
    page: int,
) -> None:
    if act == "new":
        await state.set_state(St.promo_code)
        await show(cb, "🎟 Promokod nomini yuboring (3–32 harf/raqam):", kb(back("promo", "✖️ Bekor")))
    elif act == "type":
        await state.update_data(ptype=id_)
        await state.set_state(St.promo_value)
        await show(
            cb,
            "Qiymat va limitni yuboring: <code>qiymat umumiy_limit</code>\nMasalan: <code>5 100</code> (5{} , 100 marta)".format(
                "%" if id_ == "percent" else "$"
            ),
            kb(back("promo", "✖️ Bekor")),
        )
    elif act == "off":
        p = await svc.session.get(PromoCode, int(id_))
        if p:
            p.is_active = False
        await sec_promo(cb, svc, role, user, state, rt, "open", "", 0)
    else:
        rows = (await svc.session.scalars(select(PromoCode).order_by(PromoCode.id.desc()).limit(10))).all()
        items = [
            btn(
                f"{'✅' if p.is_active else '⛔️'} {p.code} · {p.value}{'%' if p.type == PromoType.PERCENT else '$'} · {p.used_count}/{p.max_uses or '∞'}",
                Adm(sec="promo", act="off", id=str(p.id)),
                style="danger" if p.is_active else None,
            )
            for p in rows
        ]
        await show(
            cb,
            "🎟 <b>Promokodlar</b>\n(Tugmani bossangiz o'chiriladi)",
            kb(btn("➕ Yangi promokod", Adm(sec="promo", act="new"), style="success"), *items, BACK),
        )


@router.message(St.promo_code, F.text)
async def on_promo_code(m: Message, state: FSMContext) -> None:
    code = (m.text or "").strip().upper()
    if not code.isalnum() or not 3 <= len(code) <= 32:
        await m.answer("❌ 3–32 ta harf/raqam")
        return
    await state.update_data(pcode=code)
    await state.set_state(None)
    await m.answer(
        "Turi:",
        reply_markup=kb(
            [
                btn("% foiz", Adm(sec="promo", act="type", id="percent")),
                btn("$ qat'iy", Adm(sec="promo", act="type", id="fixed_usd")),
            ],
            back("promo", "✖️ Bekor"),
        ),
    )


@router.message(St.promo_value, F.text)
async def on_promo_value(m: Message, svc: Services, state: FSMContext, user: User) -> None:
    data = await state.get_data()
    await state.clear()
    parts = (m.text or "").replace(",", ".").split()
    try:
        value = D(parts[0])
        max_uses = int(parts[1]) if len(parts) > 1 else None
        await AdminService(svc.session, svc.settings).create_promo(
            user.id, data["pcode"], PromoType(data["ptype"]), value, max_uses=max_uses, applies_to=ProductScope.ALL
        )
    except (ValueError, InvalidOperation, IndexError, AppError) as exc:
        await m.answer(f"❌ {getattr(exc, 'message', exc)}", reply_markup=kb(back("promo")))
        return
    await m.answer(
        f"✅ <code>{data['pcode']}</code> yaratildi", reply_markup=kb(btn("« Promokodlar", Adm(sec="promo")))
    )


# ---------------- channels ----------------
async def sec_chan(
    cb: CallbackQuery,
    svc: Services,
    role: AdminRole,
    user: User,
    state: FSMContext,
    rt: Runtime,
    act: str,
    id_: str,
    page: int,
) -> None:
    if act == "add":
        await state.set_state(St.channel)
        await show(
            cb,
            "➕ Kanal username'ini (<code>@kanal</code>) yoki ID'sini yuboring.\nBot kanalda <b>admin</b> bo'lishi shart.",
            kb(back("chan", "✖️ Bekor")),
        )
    elif act == "del":
        c = await svc.session.get(Channel, int(id_))
        if c:
            await svc.session.delete(c)
        await sec_chan(cb, svc, role, user, state, rt, "open", "", 0)
    elif act == "toggle":
        await svc.settings.set(
            "bot.mandatory_subscription", not await svc.settings.get("bot.mandatory_subscription"), user.id
        )
        await sec_chan(cb, svc, role, user, state, rt, "open", "", 0)
    else:
        chans = (await svc.session.scalars(select(Channel))).all()
        on = bool(await svc.settings.get("bot.mandatory_subscription"))
        text = f"📢 <b>Majburiy obuna</b>\nHolat: {'✅ yoqilgan' if on else '⛔️ o`chiq'}\n" + (
            "\n".join(f"• {c.title} (<code>{c.chat_id}</code>)" for c in chans)
            or "Kanallar yo'q — tekshiruv o'tkazib yuboriladi."
        )
        await show(
            cb,
            text,
            kb(
                btn("➕ Kanal qo'shish", Adm(sec="chan", act="add"), style="success"),
                *[btn(f"🗑 {c.title}", Adm(sec="chan", act="del", id=str(c.id)), style="danger") for c in chans],
                btn("⛔️ O'chirish" if on else "✅ Yoqish", Adm(sec="chan", act="toggle")),
                BACK,
            ),
        )


@router.message(St.channel)
async def on_channel(m: Message, svc: Services, state: FSMContext, user: User, rt: Runtime) -> None:
    await state.clear()
    bot: Bot | None = rt.bot
    if bot is None:
        await m.answer("Bot ulanmagan")
        return
    origin_chat = getattr(m.forward_origin, "chat", None)
    ref: Any = origin_chat.id if origin_chat else (m.text or "").strip()
    try:
        chat = await bot.get_chat(ref)
        me = await bot.get_chat_member(chat.id, bot.id)
        if me.status not in ("administrator", "creator"):
            raise ValueError("bot admin emas")
        link = (
            f"https://t.me/{chat.username}"
            if chat.username
            else (await bot.create_chat_invite_link(chat.id)).invite_link
        )
        await AdminService(svc.session, svc.settings).add_channel(user.id, chat.id, chat.title or str(chat.id), link)
    except Exception as exc:  # noqa: BLE001
        await m.answer(f"❌ Qo'shib bo'lmadi: {str(exc)[:120]}", reply_markup=kb(back("chan")))
        return
    await m.answer("✅ Kanal qo'shildi", reply_markup=kb(btn("« Kanallar", Adm(sec="chan"))))


# ---------------- admins ----------------
async def sec_admins(
    cb: CallbackQuery,
    svc: Services,
    role: AdminRole,
    user: User,
    state: FSMContext,
    rt: Runtime,
    act: str,
    id_: str,
    page: int,
) -> None:
    if role != AdminRole.OWNER:
        await toast(cb, "Faqat owner", alert=True)
        return
    if act == "add":
        await state.set_state(St.admin_user)
        await state.update_data(mode="admin")
        await show(
            cb,
            "👮 Foydalanuvchi ID va rolni yuboring: <code>123456789 admin</code> (rollar: admin, support).\nFoydalanuvchi botni avval ishga tushirgan bo'lishi kerak.",
            kb(back("admins", "✖️ Bekor")),
        )
    elif act == "del":
        await ask_confirm(
            cb, f"🗑 Adminni olib tashlash: <code>{id_}</code>", "admin_del", {"user_id": int(id_)}, user.id
        )
    else:
        admins = await AdminService(svc.session, svc.settings).list_admins()
        await show(
            cb,
            "👮 <b>Adminlar</b>\n" + "\n".join(f"• <code>{a['user_id']}</code> — {a['role']}" for a in admins),
            kb(
                btn("➕ Admin qo'shish", Adm(sec="admins", act="add"), style="success"),
                *[
                    btn(f"🗑 {a['user_id']}", Adm(sec="admins", act="del", id=str(a["user_id"])), style="danger")
                    for a in admins
                    if a["role"] != "owner"
                ],
                BACK,
            ),
        )


@router.message(St.admin_user, F.text)
async def on_admin_user(m: Message, svc: Services, state: FSMContext, user: User, role: AdminRole) -> None:
    data = await state.get_data()
    await state.clear()
    parts = (m.text or "").split()
    try:
        if data.get("mode") == "unmatched":
            uid = None if parts[0].lower() == "ignore" else int(parts[0])
            row = await AdminService(svc.session, svc.settings).resolve_unmatched(
                user.id, data["um"], uid, await svc.rates.ton_usd()
            )
            await m.answer(f"✅ {row.resolution}", reply_markup=kb(back("fin")))
            return
        if role != AdminRole.OWNER:
            return
        await AdminService(svc.session, svc.settings).add_admin(
            user.id, int(parts[0]), AdminRole(parts[1] if len(parts) > 1 else "admin")
        )
    except (ValueError, IndexError, AppError) as exc:
        await m.answer(f"❌ {getattr(exc, 'message', exc)}", reply_markup=kb(BACK))
        return
    await m.answer("✅ Saqlandi", reply_markup=kb(btn("« Adminlar", Adm(sec="admins"))))


# ---------------- broadcast wizard ----------------
def content_from_message(m: Message) -> dict[str, Any]:
    text = m.html_text if (m.text or m.caption) else ""
    if m.photo:
        return {"type": "photo", "media_file_id": m.photo[-1].file_id, "text": text}
    if m.video:
        return {"type": "video", "media_file_id": m.video.file_id, "text": text}
    if m.animation:
        return {"type": "animation", "media_file_id": m.animation.file_id, "text": text}
    return {"type": "text", "text": text}


@router.message(St.bc_content)
async def on_bc_content(m: Message, state: FSMContext) -> None:
    content = content_from_message(m)
    if content["type"] == "text" and not content["text"]:
        await m.answer("❌ Matn, rasm, video yoki GIF yuboring")
        return
    await state.update_data(content=content)
    await state.set_state(St.bc_buttons)
    await m.answer(
        "🔘 Tugma qo'shasizmi? Har qatorda bitta: <code>Matn - https://havola</code>",
        reply_markup=kb(btn("⏭ Tugmasiz", Adm(sec="bc", act="nobtn")), back("bc", "✖️ Bekor")),
    )


@router.message(St.bc_buttons, F.text)
async def on_bc_buttons(m: Message, state: FSMContext) -> None:
    rows = []
    for line in (m.text or "").splitlines():
        if " - " in line and line.rsplit(" - ", 1)[1].strip().startswith(("http://", "https://", "tg://")):
            label, url = line.rsplit(" - ", 1)
            rows.append([{"text": label.strip(), "url": url.strip()}])
    if not rows:
        await m.answer("❌ Format: <code>Matn - https://havola</code>")
        return
    data = await state.get_data()
    content = dict(data["content"])
    content["buttons"] = rows
    await state.update_data(content=content)
    await state.set_state(None)
    await segment_screen(m)


async def segment_screen(ev: Message | CallbackQuery) -> None:
    await show(ev, "👥 Kimga yuboramiz?", kb(
        [btn("👥 Hammaga", Adm(sec="bc", act="seg", id="all"), style="primary")],
        [btn("🇺🇿 uz", Adm(sec="bc", act="seg", id="uz")), btn("🇷🇺 ru", Adm(sec="bc", act="seg", id="ru")), btn("🇬🇧 en", Adm(sec="bc", act="seg", id="en"))],
        [btn("💰 Xaridorlar", Adm(sec="bc", act="seg", id="buyers")), btn("😴 30 kun nofaol", Adm(sec="bc", act="seg", id="inactive"))],
        [btn("🆕 7 kunlik yangilar", Adm(sec="bc", act="seg", id="new7"))],
        back("bc", "✖️ Bekor"),
    ))  # fmt: skip


async def sec_bc(
    cb: CallbackQuery,
    svc: Services,
    role: AdminRole,
    user: User,
    state: FSMContext,
    rt: Runtime,
    act: str,
    id_: str,
    page: int,
) -> None:
    bs = BroadcastService(svc.session, rt.messenger)
    if act == "new":
        await state.set_state(St.bc_content)
        await show(
            cb, "📣 Xabarni yuboring (matn, rasm, video yoki GIF — formatlash saqlanadi):", kb(back("bc", "✖️ Bekor"))
        )
    elif act == "nobtn":
        await state.set_state(None)
        await segment_screen(cb)
    elif act == "seg":
        seg_map: dict[str, dict[str, Any]] = {
            "all": {},
            "uz": {"language": ["uz"]},
            "ru": {"language": ["ru"]},
            "en": {"language": ["en"]},
            "buyers": {"has_orders": True},
            "inactive": {"inactive_days": 30},
            "new7": {"registered_after": (now_utc() - timedelta(days=7)).isoformat()},
        }
        seg = seg_map[id_]  # fmt: skip
        content = (await state.get_data()).get("content")
        if not content:
            await toast(cb, "Avval xabarni yuboring", alert=True)
            return
        b = await bs.create(user.id, content, seg)
        await state.update_data(bid=b.id)
        await bs.send_test(b, user.id)
        await show(
            cb,
            f"👆 Oldindan ko'rish yuqorida.\nQabul qiluvchilar: <b>~{b.total}</b>",
            kb(
                btn("🧪 O'zimga test", Adm(sec="bc", act="test", id=str(b.id))),
                btn("🚀 Yuborish", Adm(sec="bc", act="go", id=str(b.id)), style="success"),
                btn("✖️ Bekor", Adm(sec="bc", act="cancel", id=str(b.id)), style="danger"),
            ),
        )
    elif act == "test":
        await bs.send_test(await bs.get(int(id_)), user.id)
    elif act == "go":
        b = await bs.get(int(id_))
        await ask_confirm(
            cb, f"🚀 <b>{b.total}</b> kishiga xabar yuborilsinmi?", "bc_start", {"id": b.id}, user.id, danger=False
        )
    elif act in ("pause", "cancel", "prog", "resume"):
        b = await bs.get(int(id_))
        if act == "pause" and b.status == BroadcastStatus.RUNNING:
            await bs.pause(b)
        elif act == "resume" and b.status == BroadcastStatus.PAUSED:
            await bs.start(b)
        elif act == "cancel" and b.status not in (BroadcastStatus.COMPLETED, BroadcastStatus.CANCELLED):
            await bs.cancel(b)
        p = await bs.progress(b)
        rows = [btn("🔄 Yangilash", Adm(sec="bc", act="prog", id=id_))]
        if b.status == BroadcastStatus.RUNNING:
            rows += [
                btn("⏸ To'xtatish", Adm(sec="bc", act="pause", id=id_)),
                btn("⏹ Bekor qilish", Adm(sec="bc", act="cancel", id=id_), style="danger"),
            ]
        elif b.status == BroadcastStatus.PAUSED:
            rows.append(btn("▶️ Davom ettirish", Adm(sec="bc", act="resume", id=id_), style="success"))
        await show(
            cb,
            f"📣 <b>#{b.id}</b> · {p['status']}\n{b.sent + b.failed} / {b.total} ({p['percent']}%) · ❌ {b.failed}",
            kb(rows[:1], rows[1:], back("bc")),
        )
    else:
        from app.models import Broadcast

        last = (await svc.session.scalars(select(Broadcast).order_by(Broadcast.id.desc()).limit(5))).all()
        await show(
            cb,
            "📣 <b>Xabar yuborish</b>",
            kb(
                btn("➕ Yangi xabar", Adm(sec="bc", act="new"), style="success"),
                *[
                    btn(f"#{b.id} · {b.status.value} · {b.sent}/{b.total}", Adm(sec="bc", act="prog", id=str(b.id)))
                    for b in last
                ],
                BACK,
            ),
        )


# ---------------- confirmed actions ----------------
async def _act_order(svc: Services, actor: User, role: AdminRole, p: dict[str, Any], kind: str) -> str:
    f = await svc.fulfillment()
    o = await OrderService(svc.session).by_public_id(p["id"])
    who = f"admin:{actor.id}"
    if kind == "retry":
        await f.retry(o, who)
    elif kind == "refund":
        await f.refund(o, who)
    else:
        await f.mark_completed_manually(o, who)
    await AdminService(svc.session, svc.settings).audit.log(actor.id, f"order.{kind}", "order", o.public_id)
    return f"✅ {o.public_id}: {o.status.value}"


async def run_action(action: str, p: dict[str, Any], svc: Services, actor: User, role: AdminRole) -> str:
    admin = AdminService(svc.session, svc.settings)
    if action.startswith("order_"):
        if action != "order_retry" and not has(role, AdminRole.ADMIN):
            raise AppError("ruxsat yo'q")
        return await _act_order(svc, actor, role, p, action[6:])
    if not has(role, AdminRole.ADMIN):
        raise AppError("ruxsat yo'q")
    if action == "balance":
        after = await admin.adjust_balance(actor.id, role, p["user_id"], D(p["amount"]), p.get("comment"))
        return f"✅ Yangi balans: {after:.2f} $"
    if action == "ban":
        await admin.ban(actor.id, p["user_id"], p.get("reason"))
        return "⛔️ Bloklandi"
    if action == "unban":
        await admin.unban(actor.id, p["user_id"])
        return "✅ Blokdan chiqarildi"
    if action == "maint_toggle":
        new = not await svc.settings.get("bot.maintenance")
        await svc.settings.set("bot.maintenance", new, actor.id)
        await admin.audit.log(actor.id, "settings.maintenance", "setting", "bot.maintenance", None, new)
        return f"🛠 Texnik ishlar: {'YOQILDI' if new else 'o`chirildi'}"
    if action == "bc_start":
        bs = BroadcastService(svc.session, svc.rt.messenger)
        b = await bs.get(p["id"])
        await bs.start(b)
        await admin.audit.log(actor.id, "broadcast.start", "broadcast", b.id)
        return f"🚀 Boshlandi (#{b.id}): jarayon /admin → 📣 Xabar yuborish"
    if role != AdminRole.OWNER:
        raise AppError("faqat owner")
    if action == "withdraw":
        tx = await svc.hot_wallet().withdraw_to_admin(D(p["amount"]), actor.id, role)
        return f"✅ Yuborildi: <a href='https://tonviewer.com/transaction/{tx}'>tx</a>"
    if action == "sweep_toggle":
        new = not await svc.settings.get("hot_wallet.sweep_enabled")
        await svc.settings.set("hot_wallet.sweep_enabled", new, actor.id)
        await admin.audit.log(actor.id, "settings.sweep", "setting", "hot_wallet.sweep_enabled", None, new)
        return f"🔁 Avto-o'tkazish: {'yoqildi' if new else 'o`chirildi'}"
    if action == "admin_del":
        await admin.remove_admin(actor.id, p["user_id"])
        return "🗑 Olib tashlandi"
    raise AppError("noma'lum amal")


@router.callback_query(Cf.filter())
async def on_confirm(cb: CallbackQuery, callback_data: Cf, svc: Services, role: AdminRole, user: User) -> None:
    redis = get_redis()
    raw = await redis.getdel(f"cf:{callback_data.token}")
    if raw is None:
        await toast(cb, "⌛️ Muddati o'tgan", alert=True)
        return
    spec = json.loads(raw)
    if spec["actor"] != user.id:
        await toast(cb, "⛔️ Bu so'rov sizniki emas", alert=True)
        return
    if not callback_data.yes:
        await toast(cb, "Bekor qilindi")
        await show(cb, "Bekor qilindi.", kb(BACK))
        return
    await toast(cb)
    try:
        result = await run_action(spec["action"], spec["params"], svc, user, role)
    except AppError as exc:
        result = f"❌ {exc.message}"
    except Exception as exc:  # noqa: BLE001
        log.error("admin_action_failed", action=spec["action"], error=str(exc))
        result = f"❌ Xato: {str(exc)[:150]}"
    await show(cb, result, kb(BACK))


SECTIONS = {
    "stats": sec_stats, "orders": sec_orders, "users": sec_users, "fin": sec_fin, "price": sec_price,
    "methods": sec_methods, "ref": sec_ref, "set": sec_set, "promo": sec_promo, "chan": sec_chan,
    "admins": sec_admins, "bc": sec_bc,
}  # fmt: skip
