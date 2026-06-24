from __future__ import annotations
import feedparser
import httpx
from bs4 import BeautifulSoup
from backend.scrapers.base import BaseScraper
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class NewsScraper(BaseScraper):
    """Scraper for Gulf News and The National RSS feeds — UAE infrastructure news."""

    source_name = "UAE News (Gulf News / The National)"
    base_url = ""
    RSS_FEEDS = [
        ("https://gulfnews.com/rss/uae", "Gulf News"),
        ("https://gulfnews.com/rss/business", "Gulf News Business"),
        ("https://www.thenationalnews.com/rss/business", "The National Business"),
        ("https://www.thenationalnews.com/rss/uae", "The National UAE"),
    ]
    PPP_KEYWORDS = [
        "PPP", "public-private", "infrastructure", "project", "contract value",
        "billion", "AED", "tender", "construction", "power plant", "desalination",
        "metro", "railway", "hospital", "solar", "energy project",
        "road project", "water project", "airport", "port",
    ]

    async def scrape(self) -> list[dict]:
        results: list[dict] = []
        async with httpx.AsyncClient() as client:
            for rss_url, feed_name in self.RSS_FEEDS:
                try:
                    html = await self.fetch(rss_url, client)
                    if not html:
                        await self.rate_limit()
                        continue
                    feed = feedparser.parse(html)
                    for entry in feed.entries:
                        title = entry.get("title", "")
                        summary = entry.get("summary", "")
                        link = entry.get("link", "")
                        combined = f"{title} {summary}".lower()
                        if any(kw.lower() in combined for kw in self.PPP_KEYWORDS):
                            raw_text = f"{title}\n\nSource: {feed_name}\nURL: {link}\n\n{summary}"
                            try:
                                full_html = await self.fetch(link, client)
                                if full_html:
                                    soup = BeautifulSoup(full_html, "lxml")
                                    for tag in soup(["script", "style", "nav", "footer", "aside"]):
                                        tag.decompose()
                                    full_text = soup.get_text(separator="\n", strip=True)
                                    raw_text = f"{title}\n\nSource: {feed_name}\nURL: {link}\n\n{full_text[:5000]}"
                                await self.rate_limit()
                            except Exception as e:
                                logger.warning("news_article_fetch_failed", url=link, error=str(e))
                            results.append({
                                "name": title,
                                "url": link or rss_url,
                                "raw_text": raw_text,
                                "source_name": feed_name,
                            })
                    await self.rate_limit()
                except Exception as e:
                    logger.error("news_scrape_error", url=rss_url, feed=feed_name, error=str(e))
        logger.info("news_scrape_complete", count=len(results))
        return results
