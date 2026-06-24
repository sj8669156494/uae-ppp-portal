from __future__ import annotations
import httpx
from bs4 import BeautifulSoup
from backend.scrapers.base import BaseScraper
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class ADIOScraper(BaseScraper):
    """Scraper for Abu Dhabi Investment Office (ADIO) — PPP and investment projects."""

    source_name = "ADIO - Abu Dhabi Investment Office"
    base_url = "https://www.adio.gov.ae"
    target_paths = [
        "/en/resources/ppp-projects",
        "/en/resources/investment-opportunities",
        "/en/media/news",
    ]

    async def scrape(self) -> list[dict]:
        results: list[dict] = []
        async with httpx.AsyncClient() as client:
            for path in self.target_paths:
                url = f"{self.base_url}{path}"
                try:
                    html = await self.fetch(url, client)
                    if not html:
                        await self.rate_limit()
                        continue
                    items = self._parse_listing(html, url)
                    for item in items:
                        try:
                            detail_html = await self.fetch(item["url"], client)
                            if detail_html:
                                detail_text = self._extract_text(detail_html)
                                item["raw_text"] = f"{item['name']}\nURL: {item['url']}\n\n{detail_text[:5000]}"
                            await self.rate_limit()
                        except Exception as e:
                            logger.warning("adio_detail_failed", url=item["url"], error=str(e))
                        results.append(item)
                    await self.rate_limit()
                except Exception as e:
                    logger.error("adio_scrape_error", url=url, error=str(e))
        logger.info("adio_scrape_complete", count=len(results))
        return results

    def _parse_listing(self, html: str, source_url: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        items: list[dict] = []
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            text = anchor.get_text(strip=True)
            if not text or len(text) < 10:
                continue
            if any(kw in text.lower() for kw in ["project", "ppp", "investment", "partnership", "infrastructure"]):
                full_url = href if href.startswith("http") else f"{self.base_url}{href}"
                items.append({
                    "name": text[:200],
                    "url": full_url,
                    "raw_text": text,
                    "source_name": self.source_name,
                })
        return items[:20]

    def _extract_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
