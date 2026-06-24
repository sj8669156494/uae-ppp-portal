from __future__ import annotations
import feedparser
import httpx
from backend.scrapers.base import BaseScraper
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class WAMScraper(BaseScraper):
    """Scraper for UAE Media Office / WAM (wam.ae) RSS feed."""

    source_name = "WAM - UAE Media Office"
    base_url = "https://wam.ae"
    rss_urls = [
        "https://wam.ae/en/rss",
        "https://wam.ae/api/articles/rss?lang=en",
    ]
    PPP_KEYWORDS = [
        "PPP", "public-private", "partnership", "infrastructure", "project",
        "contract", "tender", "construction", "power plant", "desalination",
        "metro", "railway", "hospital", "school", "solar", "energy",
    ]

    async def scrape(self) -> list[dict]:
        results: list[dict] = []
        async with httpx.AsyncClient() as client:
            for rss_url in self.rss_urls:
                try:
                    html = await self.fetch(rss_url, client)
                    if not html:
                        continue
                    feed = feedparser.parse(html)
                    for entry in feed.entries:
                        title = entry.get("title", "")
                        summary = entry.get("summary", "")
                        link = entry.get("link", "")
                        combined = f"{title} {summary}".lower()
                        if any(kw.lower() in combined for kw in self.PPP_KEYWORDS):
                            raw_text = f"{title}\n\n{summary}"
                            if link:
                                try:
                                    full_text = await self.fetch(link, client)
                                    if full_text:
                                        raw_text = f"{title}\n\nURL: {link}\n\n{full_text[:5000]}"
                                    await self.rate_limit()
                                except Exception as e:
                                    logger.warning("wam_article_fetch_failed", url=link, error=str(e))
                            results.append({
                                "name": title,
                                "url": link or rss_url,
                                "raw_text": raw_text,
                                "source_name": self.source_name,
                            })
                    await self.rate_limit()
                except Exception as e:
                    logger.error("wam_scrape_error", url=rss_url, error=str(e))
        logger.info("wam_scrape_complete", count=len(results))
        return results
