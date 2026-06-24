from __future__ import annotations
import httpx
from bs4 import BeautifulSoup
from backend.scrapers.base import BaseScraper
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class DEWAScraper(BaseScraper):
    """Scraper for Dubai Electricity and Water Authority (DEWA)."""

    source_name = "DEWA - Dubai Electricity & Water Authority"
    base_url = "https://www.dewa.gov.ae"
    target_urls = [
        "https://www.dewa.gov.ae/en/about-us/media-centre/news",
        "https://www.dewa.gov.ae/en/business/projects",
        "https://www.dewa.gov.ae/en/business/tenders",
    ]
    PPP_KEYWORDS = [
        "solar", "power", "energy", "desalination", "water", "IPP", "IWPP",
        "project", "contract", "tender", "AED", "billion", "megawatt", "MW", "MIGD",
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
                    logger.error("dewa_scrape_error", url=url, error=str(e))
        logger.info("dewa_scrape_complete", count=len(results))
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
                "name": f"DEWA Projects — {source_url.split('/')[-1]}",
                "url": source_url,
                "raw_text": f"Source: DEWA\nURL: {source_url}\n\n" + "\n".join(relevant[:50]),
                "source_name": self.source_name,
            })
        return results[:10]
