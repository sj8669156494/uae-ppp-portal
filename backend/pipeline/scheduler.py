from __future__ import annotations
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from backend.config import settings
from backend.utils.logging import get_logger

logger = get_logger(__name__)

scheduler = AsyncIOScheduler()


async def run_all_scrapers() -> None:
    """Run all scrapers and push results through the pipeline."""
    from datetime import datetime, timezone
    from backend.api.health import set_last_scraper_run
    logger.info("scraper_job_start")
    try:
        from backend.scrapers.wam import WAMScraper
        from backend.scrapers.adio import ADIOScraper
        from backend.scrapers.news import NewsScraper
        from backend.db.session import AsyncSessionLocal
        from backend.pipeline.extractor import ProjectExtractor
        from backend.pipeline.cleaner import ProjectCleaner

        scraper_classes = [WAMScraper, ADIOScraper, NewsScraper]
        extractor = ProjectExtractor()
        cleaner = ProjectCleaner()

        async with AsyncSessionLocal() as session:
            for ScraperClass in scraper_classes:
                try:
                    scraper = ScraperClass()
                    raw_items = await scraper.scrape()
                    for item in raw_items:
                        try:
                            project_data = await extractor.extract(item["raw_text"], item["url"])
                            cleaned = cleaner.clean(project_data)
                            if cleaned:
                                from backend.db.crud import upsert_project
                                await upsert_project(session, cleaned)
                        except Exception as e:
                            logger.warning("extract_failed", error=str(e), url=item.get("url"))
                    await session.commit()
                except Exception as e:
                    logger.error("scraper_failed", scraper=ScraperClass.__name__, error=str(e))
    except Exception as e:
        logger.error("scraper_job_error", error=str(e))
    set_last_scraper_run(datetime.now(timezone.utc).isoformat())
    logger.info("scraper_job_complete")


def start_scheduler() -> None:
    scheduler.add_job(
        run_all_scrapers,
        CronTrigger(
            hour=settings.scraper_schedule_hour,
            minute=settings.scraper_schedule_minute,
        ),
        id="daily_scrapers",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("scheduler_started", hour=settings.scraper_schedule_hour)


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
    logger.info("scheduler_stopped")
