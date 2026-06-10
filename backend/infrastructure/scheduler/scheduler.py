from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from logger import get_logger

log = get_logger(__name__)

_scheduler: AsyncIOScheduler | None = None


def start_scheduler(layer1_run_fn, layer2_refresh_fn, discussion_crawl_fn):
    global _scheduler
    _scheduler = AsyncIOScheduler()

    layer1_trigger = CronTrigger(hour=9, minute=0, timezone="Asia/Ho_Chi_Minh")
    _scheduler.add_job(
        _safe_run,
        layer1_trigger,
        id="layer1_run",
        replace_existing=True,
        kwargs={"fn": layer1_run_fn, "label": "Layer 1 run"},
    )

    # Layer 2 runs every 5 min from 09:15 to 15:00
    layer2_trigger = CronTrigger(
        hour="9-14", minute="*/5", timezone="Asia/Ho_Chi_Minh"
    )
    _scheduler.add_job(
        _safe_run_if_trading,
        layer2_trigger,
        id="layer2_refresh",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        kwargs={"fn": layer2_refresh_fn, "label": "Layer 2 refresh"},
    )

    discussion_trigger = CronTrigger(minute="*/30", timezone="Asia/Ho_Chi_Minh")
    _scheduler.add_job(
        _safe_run,
        discussion_trigger,
        id="discussion_crawl",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        kwargs={"fn": discussion_crawl_fn, "label": "Discussion crawl"},
    )

    _scheduler.start()
    log.info(
        "Scheduler started: layer1 at 09:00, "
        "layer2 refresh 09:15–15:00 every 5 min, "
        "discussion crawl every 30 min (Asia/Ho_Chi_Minh)"
    )


async def _safe_run(fn, label: str):
    try:
        await fn()
    except ValueError as e:
        log.warning("%s skipped: %s", label, e)
    except Exception:
        log.error("%s failed", label, exc_info=True)


async def _safe_run_if_trading(fn, label: str):
    from datetime import datetime
    import pytz
    now = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
    # Run only 09:15–15:00
    start = now.replace(hour=9, minute=15, second=0, microsecond=0)
    end   = now.replace(hour=15, minute=0, second=0, microsecond=0)
    if not (start <= now <= end):
        log.debug("%s skipped: outside trading window %s", label, now.strftime("%H:%M"))
        return
    await _safe_run(fn, label)


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        log.info("Scheduler stopped")
