from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from logger import get_logger

log = get_logger(__name__)

_scheduler: AsyncIOScheduler | None = None


def start_scheduler(crawl_fn):
    global _scheduler
    _scheduler = AsyncIOScheduler()
    # Run daily at 16:00 Vietnam time (UTC+7) — after market close at 15:00
    trigger = CronTrigger(hour=16, minute=0, timezone="Asia/Ho_Chi_Minh")
    _scheduler.add_job(crawl_fn, trigger, id="daily_crawl", replace_existing=True)
    _scheduler.start()
    log.info("Scheduler started: daily crawl at 16:00 Asia/Ho_Chi_Minh")


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        log.info("Scheduler stopped")
