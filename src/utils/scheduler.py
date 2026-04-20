"""APScheduler-based daily data collection scheduler.

Start alongside the API server:
    python -m src.utils.scheduler
"""

import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from src.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def job_collect_fred():
    from src.collectors.fred import collect
    logger.info("Scheduled: FRED collection starting")
    collect()


def job_collect_market():
    from src.collectors.market import collect
    logger.info("Scheduled: Market data collection starting")
    collect()


def job_collect_news():
    from src.collectors.news import NewsCollector
    logger.info("Scheduled: News collection starting")
    collector = NewsCollector()
    articles = collector.collect()
    logger.info("Collected %d relevant articles", len(articles))


def build_scheduler() -> BlockingScheduler:
    scheduler = BlockingScheduler(timezone="America/New_York")

    # FRED macro data: weekdays at 08:00 ET (before US market open)
    scheduler.add_job(job_collect_fred,   CronTrigger(day_of_week="mon-fri", hour=8,  minute=0))
    # Market data: weekdays at 17:00 ET (after US market close)
    scheduler.add_job(job_collect_market, CronTrigger(day_of_week="mon-fri", hour=17, minute=30))
    # News: every 4 hours on weekdays
    scheduler.add_job(job_collect_news,   CronTrigger(day_of_week="mon-fri", hour="6,10,14,18,22"))

    return scheduler


if __name__ == "__main__":
    scheduler = build_scheduler()
    logger.info("Scheduler started — press Ctrl+C to stop")
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped")
