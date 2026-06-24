from __future__ import annotations
import httpx
from bs4 import BeautifulSoup
from backend.scrapers.base import BaseScraper
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class RTAScraper(BaseScraper):
    """Scraper for Roads and Transport Authority (RTA) Dubai."""

    source_name = "RTA Dubai"
    base_url = "https://www.rta.ae"
    target_urls = [
        "https://www.rta.ae/wps/portal/rta/ae/public-transport/projects",
        "https://www.rta.ae/wps/portal/rta/ae/news/news-listing",
        "https://www.rta.ae/wps/portal/rta/ae/home/contracts-and-tenders",
    ]
    PPP_KEYWORDS = [
        "project", "contract", "tender", "metro", "tram", "bus", "road",
        "bridge", "tunnel", "infrastructure", "AED", "billion", "million",
    ]

    async def scrape(self) -> list[dict]:
        results: list[dict] = []
        async with httpx.AsyncClient() as client:
            for url in self.target_urls:
                try:
                    html = await self.fetch(url, client)
                    if not html:
                        await self.rate_limit()
                        continue
                    items = self._parse(html, url)
                    results.extend(items)
                    await self.rate_limit()
                except Exception as e:
                    logger.error("rta_scrape_error", url=url, error=str(e))
        logger.info("rta_scrape_complete", count=len(results))
        return results

    def _parse(self, html: str, source_url: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        lines = [l for l in text.split("\n") if len(l.strip()) > 30]
        relevant = [l for l in lines if any(kw.lower() in l.lower() for kw in self.PPP_KEYWORDS)]

        results: list[dict] = []
        if relevant:
            results.append({
                "name": f"RTA Dubai Projects — {source_url.split('/')[-1]}",
                "url": source_url,
                "raw_text": f"Source: RTA Dubai\nURL: {source_url}\n\n" + "\n".join(relevant[:50]),
                "source_name": self.source_name,
            })

        for anchor in soup.find_all("a", href=True):
            text = anchor.get_text(strip=True)
            href = anchor["href"]
            if len(text) > 15 and any(kw.lower() in text.lower() for kw in self.PPP_KEYWORDS):
                full_url = href if href.startswith("http") else f"{self.base_url}{href}"
                results.append({
                    "name": text[:200],
                    "url": full_url,
                    "raw_text": f"RTA Project: {text}\nURL: {full_url}",
                    "source_name": self.source_name,
                })

        return results[:15]
