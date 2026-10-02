"""Background jobs. Each job opens its own session and is safe to run concurrently (advisory/row locks)."""

from datetime import timedelta
from decimal import Decimal

import structlog
from sqlalchemy import func, select

from app.api.runtime import Runtime, Services, build_providers
from app.core.db import session_maker
from app.core.enums import BroadcastStatus
from app.core.redis import get_redis
from app.core.timeutil import now_utc, today_local, tz
from app.models import BalanceTransaction, Broadcast, User
from app.services.admin_service import AdminService
from app.services.analytics_service import AnalyticsService, resolve_period
from app.services.broadcast_service import BroadcastService
from app.services.report_service import format_stats

log = structlog.get_logger()
LOCKS = {"ton_watcher": 7001, "hot_wallet": 7002, "stats": 7003, "broadcast": 7004, "rates": 7005}


async def _lock(session, name: str) -> bool:  # type: ignore[no-untyped-def]
    return bool(await session.scalar(select(func.pg_try_advisory_xact_lock(LOCKS[name]))))


async def ton_watcher(rt: Runtime) -> None:
    async with session_maker()() as s:
        svc = Services(s, rt)
        address = await svc.settings.get("hot_wallet.address")
        if not address or not await _lock(s, "ton_watcher"):
            return
        last = int(await svc.settings.get("ton_watcher.last_lt") or 0)
        txs = await rt.get_chain().get_incoming(str(address), last)
        for tx in sorted(txs, key=lambda t: t.lt):
            await svc.checkout.payments.process_incoming(tx)
            last = max(last, tx.lt)
        await svc.settings.set("ton_watcher.last_lt", last)
        await s.commit()


async def fulfillment(rt: Runtime) -> None:
    for _ in range(20):
        async with session_maker()() as s:
            svc = Services(s, rt)
            if not await (await svc.fulfillment()).process_next():
                return


async def fulfillment_recovery(rt: Runtime) -> None:
    async with session_maker()() as s:
        n = await (await Services(s, rt).fulfillment()).recover_stuck()
        await s.commit()
        if n:
            log.warning("recovered_stuck_orders", count=n)


async def expirer(rt: Runtime) -> None:
    async with session_maker()() as s:
        await Services(s, rt).checkout.payments.expire_stale()
        await s.commit()


async def rates(rt: Runtime) -> None:
    async with session_maker()() as s:
        if not await _lock(s, "rates"):
            return
        svc = Services(s, rt)
        pairs = ["TON_USD"]
        redis = get_redis()
        if not await redis.get("rate:USD_UZS"):
            pairs.append("USD_UZS")
        got = await svc.rates.refresh(pairs)
        if "USD_UZS" in got:
            await redis.set("rate:USD_UZS", str(got["USD_UZS"]), ex=6 * 3600)
        await s.commit()


async def provider_prices(rt: Runtime) -> None:
    async with session_maker()() as s:
        svc = Services(s, rt)
        providers = list((await build_providers(svc.settings, rt)).values())
        await AdminService(s, svc.settings).refresh_provider_prices(providers)
        await s.commit()


async def stars_balance(rt: Runtime) -> None:
    if rt.stars is None:
        return
    await get_redis().set("stars:balance", str(await rt.stars.star_balance()), ex=3600)


async def hot_wallet(rt: Runtime) -> None:
    async with session_maker()() as s:
        svc = Services(s, rt)
        if not await svc.settings.get("hot_wallet.address") or not await _lock(s, "hot_wallet"):
            return
        hw = svc.hot_wallet()
        balance = await hw.balance()
        low = Decimal(str(await svc.settings.get("hot_wallet.low_balance_alert_ton")))
        redis = get_redis()
        if balance < low and not await redis.get("alert:hw_low"):
            await redis.set("alert:hw_low", "1", ex=3600)
            await svc.notifier.alert(
                f"Hot wallet balansi past: {balance} TON (chegara {low}). To'ldiring: <code>{hw.signer.address if hw.signer else await hw.address()}</code>",
                "crit",
            )
        if await hw.auto_sweep():
            log.info("auto_sweep_done")
        await s.commit()


async def stats(rt: Runtime) -> None:
    async with session_maker()() as s:
        if not await _lock(s, "stats"):
            return
        a = AnalyticsService(s)
        today = today_local()
        await a.compute_day(today)
        await a.compute_day(today - timedelta(days=1))
        await s.commit()


async def broadcast(rt: Runtime) -> None:
    async with session_maker()() as s:
        if not await _lock(s, "broadcast"):
            return
        svc = BroadcastService(s, rt.messenger)
        await svc.activate_due()
        running = (await s.scalars(select(Broadcast).where(Broadcast.status == BroadcastStatus.RUNNING))).all()
        for b in running:
            await svc.send_batch(b)
        await s.commit()


async def reports(rt: Runtime) -> None:
    """Daily 23:55, weekly Monday 09:00, monthly 1st 09:00 — sent to the log chat."""
    now = now_utc().astimezone(tz())
    redis = get_redis()
    jobs: list[tuple[str, str, str]] = []
    if (now.hour, now.minute) >= (23, 55):
        jobs.append((f"report:daily:{now.date()}", "today", "Kunlik hisobot"))
    if now.weekday() == 0 and now.hour >= 9:
        jobs.append((f"report:weekly:{now.date()}", "last_week", "Haftalik hisobot"))
    if now.day == 1 and now.hour >= 9:
        jobs.append((f"report:monthly:{now.date()}", "last_month", "Oylik hisobot"))
    for key, period, title in jobs:
        if not await redis.set(key, "1", nx=True, ex=3 * 86400):
            continue
        async with session_maker()() as s:
            svc = Services(s, rt)
            today = today_local()
            if period == "today":
                p = resolve_period("today")
            elif period == "last_week":
                start = today - timedelta(days=today.weekday() + 7)
                p = resolve_period("custom", start, start + timedelta(days=6))
            else:
                last = today.replace(day=1) - timedelta(days=1)
                p = resolve_period("custom", last.replace(day=1), last)
            a = AnalyticsService(s)
            data = await a.dashboard(p)
            await svc.notifier.alert(format_stats(title, data, await a.dau_wau_mau()), "info")
            await s.commit()


async def reconciliation(rt: Runtime) -> None:
    async with session_maker()() as s:
        svc = Services(s, rt)
        ledger = await s.scalar(select(func.coalesce(func.sum(BalanceTransaction.amount_usd), 0)))
        balances = await s.scalar(select(func.coalesce(func.sum(User.balance_usd), 0)))
        if ledger != balances:
            await svc.notifier.alert(f"Balans ledgeri mos emas: ledger={ledger}, balans={balances}", "crit")


async def fragment_health(rt: Runtime) -> None:
    async with session_maker()() as s:
        svc = Services(s, rt)
        providers = await build_providers(svc.settings, rt)
        from app.core.enums import ProviderCode

        p = providers.get(ProviderCode.FRAGMENT_DIRECT)
        if p is None or not await p.is_available():
            return
        try:
            await p.resolve_recipient("telegram", "premium", 3)
        except Exception as exc:  # noqa: BLE001
            redis = get_redis()
            if not await redis.get("alert:fragment"):
                await redis.set("alert:fragment", "1", ex=6 * 3600)
                await svc.notifier.alert(
                    f"Fragment sessiyasi ishlamayapti: {exc}. ⚙️ Sozlamalar → 🔐 Fragment orqali cookie yangilang.",
                    "crit",
                )


async def heartbeat(rt: Runtime) -> None:
    await get_redis().set("worker:heartbeat", now_utc().isoformat(), ex=120)
