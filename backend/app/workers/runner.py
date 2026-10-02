import asyncio
import signal
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import structlog

from app.api.runtime import Runtime, runtime
from app.core.logging import setup_logging
from app.workers import jobs

log = structlog.get_logger()
Job = Callable[[Runtime], Awaitable[None]]


@dataclass
class Schedule:
    name: str
    fn: Job
    interval: float


SCHEDULES = [
    Schedule("ton_watcher", jobs.ton_watcher, 5),
    Schedule("fulfillment", jobs.fulfillment, 2),
    Schedule("fulfillment_recovery", jobs.fulfillment_recovery, 60),
    Schedule("expirer", jobs.expirer, 60),
    Schedule("rates", jobs.rates, 60),
    Schedule("provider_prices", jobs.provider_prices, 600),
    Schedule("stars_balance", jobs.stars_balance, 600),
    Schedule("hot_wallet", jobs.hot_wallet, 120),
    Schedule("stats", jobs.stats, 300),
    Schedule("broadcast", jobs.broadcast, 1.5),
    Schedule("reports", jobs.reports, 60),
    Schedule("reconciliation", jobs.reconciliation, 86400),
    Schedule("fragment_health", jobs.fragment_health, 1800),
    Schedule("heartbeat", jobs.heartbeat, 30),
]


async def supervise(sched: Schedule, rt: Runtime, stop: asyncio.Event) -> None:
    failures = 0
    while not stop.is_set():
        try:
            await sched.fn(rt)
            failures = 0
            delay = sched.interval
        except Exception as exc:  # noqa: BLE001 - a job must never take the worker down
            failures += 1
            delay = min(sched.interval * 2**failures, 300)
            log.error("job_failed", job=sched.name, error=str(exc), failures=failures)
            if failures == 3:
                try:
                    from app.api.runtime import Services
                    from app.core.db import session_maker

                    async with session_maker()() as s:
                        await Services(s, rt).notifier.alert(
                            f"Worker job <b>{sched.name}</b> 3 marta yiqildi: {str(exc)[:200]}", "crit"
                        )
                except Exception:  # noqa: BLE001
                    pass
        try:
            await asyncio.wait_for(stop.wait(), timeout=delay)
        except TimeoutError:
            pass


async def main(rt: Runtime | None = None) -> None:
    setup_logging()
    rt = rt or runtime()
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    log.info("worker_started", jobs=[s.name for s in SCHEDULES])
    await asyncio.gather(*(supervise(s, rt, stop) for s in SCHEDULES))
    log.info("worker_stopped")


if __name__ == "__main__":
    from app.bot.setup import build_runtime

    asyncio.run(main(build_runtime()))
