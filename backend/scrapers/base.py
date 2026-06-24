from __future__ import annotations
import asyncio
from abc import ABC, abstractmethod
import httpx
from backend.config import settings
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class BaseScraper(ABC):
    """Abstract base class for all UAE PPP scrapers."""

    source_name: str = ""
    base_url: str = ""

    def __init__(self) -> None:
        self.headers = {
            "User-Agent": settings.scraper_user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.delay = settings.scraper_delay_seconds
        self.timeout = settings.scraper_timeout_seconds
        self.max_retries = settings.max_retries

    @abstractmethod
    async def scrape(self) -> list[dict]:
        """Scrape data and return list of raw dicts with at minimum name, url, raw_text."""
        ...

    async def fetch(self, url: str, client: httpx.AsyncClient) -> str:
        """Fetch a URL with retry logic and rate limiting."""
        for attempt in range(1, self.max_retries + 1):
            try:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout,
                    follow_redirects=True,
                )
                response.raise_for_status()
                logger.info("fetch_ok", url=url, status=response.status_code)
                return response.text
            except httpx.HTTPStatusError as e:
                logger.warning("fetch_http_error", url=url, status=e.response.status_code, attempt=attempt)
                if e.response.status_code in (403, 404, 410):
                    return ""
            except (httpx.RequestError, httpx.TimeoutException) as e:
                logger.warning("fetch_error", url=url, error=str(e), attempt=attempt)
            if attempt < self.max_retries:
                await asyncio.sleep(self.delay * attempt)
        return ""

    async def fetch_with_client(self, url: str) -> str:
        async with httpx.AsyncClient() as client:
            return await self.fetch(url, client)

    async def rate_limit(self) -> None:
        await asyncio.sleep(self.delay)
