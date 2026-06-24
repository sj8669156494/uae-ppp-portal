from __future__ import annotations
import httpx
from bs4 import BeautifulSoup
from backend.scrapers.base import BaseScraper
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class DubaiDOFScraper(BaseScraper):
    """Scraper for Dubai Department of Finance PPP portal."""

    source_name = "Dubai DOF - PPP"
    base_url = "https://www.dof.gov.ae"
    target_urls = [
        "https://www.dof.gov.ae/en/ppp",
        "https://www.dof.gov.ae/en/ppp/ppp-projects",
        "https://www.dof.gov.ae/en/ppp/news",
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
                    items = self._parse_projects(html, url)
                    results.extend(items)
                    await self.rate_limit()
                except Exception as e:
                    logger.error("dubai_dof_scrape_error", url=url, error=str(e))
        logger.info("dubai_dof_scrape_complete", count=len(results))
        return results

    def _parse_projects(self, html: str, source_url: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        items: list[dict] = []

        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        full_text = soup.get_text(separator="\n", strip=True)
        paragraphs = [p for p in full_text.split("\n") if len(p.strip()) > 50]

        project_keywords = ["project", "ppp", "contract", "tender", "billion", "million", "AED", "Dh"]
        relevant_sections: list[str] = []
        for i, para in enumerate(paragraphs):
            if any(kw.lower() in para.lower() for kw in project_keywords):
                start = max(0, i - 1)
                end = min(len(paragraphs), i + 3)
                relevant_sections.append("\n".join(paragraphs[start:end]))

        if relevant_sections:
            items.append({
                "name": f"Dubai DOF PPP Portal Content — {source_url.split('/')[-1]}",
                "url": source_url,
                "raw_text": f"Source: {source_url}\n\n" + "\n\n---\n\n".join(relevant_sections[:10]),
                "source_name": self.source_name,
            })

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            text = anchor.get_text(strip=True)
            if len(text) > 15 and any(kw.lower() in text.lower() for kw in project_keywords):
                full_url = href if href.startswith("http") else f"{self.base_url}{href}"
                items.append({
                    "name": text[:200],
                    "url": full_url,
                    "raw_text": f"Project link from Dubai DOF PPP portal\nTitle: {text}\nURL: {full_url}",
                    "source_name": self.source_name,
                })

        return items[:15]
