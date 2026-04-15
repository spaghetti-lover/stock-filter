from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from logger import get_logger

log = get_logger(__name__)

_scheduler: AsyncIOScheduler | None = None
_VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def start_scheduler(crawl_fn, layer2_refresh_fn=None):
    global _scheduler
    _scheduler = AsyncIOScheduler()

    # Daily crawl at 16:00 Vietnam time — after market close at 15:00
    trigger = CronTrigger(hour=16, minute=0, timezone="Asia/Ho_Chi_Minh")
    _scheduler.add_job(crawl_fn, trigger, id="daily_crawl", replace_existing=True)
    log.info("Scheduler: daily crawl at 16:00 Asia/Ho_Chi_Minh")

    # Layer 2 refresh every 5 minutes during trading hours (9:00-15:00 VN)
    if layer2_refresh_fn is not None:
        async def _guarded_layer2_refresh():
            vn_now = datetime.now(_VN_TZ)
            hour = vn_now.hour
            if hour < 9 or hour >= 15:
                log.debug("Layer2 refresh skipped: outside trading hours (%02d:%02d VN)", vn_now.hour, vn_now.minute)
                return
            try:
                await layer2_refresh_fn()
            except Exception:
                log.warning("Layer2 scheduled refresh failed", exc_info=True)

        _scheduler.add_job(
            _guarded_layer2_refresh,
            IntervalTrigger(minutes=5),
            id="layer2_refresh",
            replace_existing=True,
        )
        log.info("Scheduler: layer2 refresh every 5 min (9:00-15:00 VN)")

    _scheduler.start()


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        log.info("Scheduler stopped")
