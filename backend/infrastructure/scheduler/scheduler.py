from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from logger import get_logger

log = get_logger(__name__)

_scheduler: AsyncIOScheduler | None = None


def start_scheduler(crawl_fn, layer2_refresh_fn, discussion_crawl_fn):
    global _scheduler
    _scheduler = AsyncIOScheduler()

    crawl_trigger = CronTrigger(hour=16, minute=0, timezone="Asia/Ho_Chi_Minh")
    _scheduler.add_job(crawl_fn, crawl_trigger, id="daily_crawl", replace_existing=True)

    layer2_trigger = CronTrigger(minute="*/5", timezone="Asia/Ho_Chi_Minh")
    _scheduler.add_job(
        _safe_run,
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
        "Scheduler started: daily crawl at 16:00, layer2 refresh every 5 min, "
        "discussion crawl every 30 min (Asia/Ho_Chi_Minh)"
    )


async def _safe_run(fn, label: str):
    try:
        await fn()
    except ValueError as e:
        log.warning("%s skipped: %s", label, e)
    except Exception:
        log.error("%s failed", label, exc_info=True)


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        log.info("Scheduler stopped")
