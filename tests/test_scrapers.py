from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


WAM_SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>WAM News</title>
    <item>
      <title>Dubai awards AED 30 billion metro Blue Line project contract</title>
      <link>https://wam.ae/article/123</link>
      <description>The Roads and Transport Authority (RTA) awarded a AED 30 billion contract
      for the Dubai Metro Blue Line extension to Alstom and Acciona consortium.
      The project involves 14 new stations across 30 km.</description>
    </item>
    <item>
      <title>Sports results from weekend</title>
      <link>https://wam.ae/article/456</link>
      <description>Team wins local championship.</description>
    </item>
  </channel>
</rss>"""

ADIO_SAMPLE_HTML = """<html>
<body>
  <h1>ADIO Investment Opportunities</h1>
  <a href="/en/project/solar-energy">Abu Dhabi Solar Energy Project - AED 5 billion investment</a>
  <a href="/en/project/healthcare-ppp">Healthcare PPP Partnership Programme</a>
  <a href="/en/about">About Us</a>
</body>
</html>"""

NEWS_SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Gulf News Business</title>
    <item>
      <title>UAE awards AED 50 billion Etihad Rail contract to CRCC</title>
      <link>https://gulfnews.com/article/789</link>
      <description>The UAE has awarded a massive AED 50 billion infrastructure contract for the
      national Etihad Rail network to China Railway Construction Corporation.</description>
    </item>
    <item>
      <title>Dubai restaurant review</title>
      <link>https://gulfnews.com/article/999</link>
      <description>Best places to eat in Dubai Marina.</description>
    </item>
  </channel>
</rss>"""


@pytest.mark.asyncio
async def test_wam_scraper_filters_ppp():
    from backend.scrapers.wam import WAMScraper
    import feedparser

    scraper = WAMScraper()
    feed = feedparser.parse(WAM_SAMPLE_RSS)

    with patch.object(scraper, "fetch", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = WAM_SAMPLE_RSS
        with patch("feedparser.parse", return_value=feed):
            with patch.object(scraper, "rate_limit", new_callable=AsyncMock):
                results = await scraper.scrape()

    assert isinstance(results, list)
    ppp_titles = [r["name"] for r in results]
    assert any("metro" in t.lower() or "billion" in t.lower() for t in ppp_titles)


@pytest.mark.asyncio
async def test_wam_scraper_returns_required_fields():
    from backend.scrapers.wam import WAMScraper
    import feedparser

    scraper = WAMScraper()
    feed = feedparser.parse(WAM_SAMPLE_RSS)

    with patch.object(scraper, "fetch", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = WAM_SAMPLE_RSS
        with patch("feedparser.parse", return_value=feed):
            with patch.object(scraper, "rate_limit", new_callable=AsyncMock):
                results = await scraper.scrape()

    for result in results:
        assert "name" in result
        assert "url" in result
        assert "raw_text" in result
        assert "source_name" in result


@pytest.mark.asyncio
async def test_adio_scraper_parses_project_links():
    from backend.scrapers.adio import ADIOScraper

    scraper = ADIOScraper()
    items = scraper._parse_listing(ADIO_SAMPLE_HTML, "https://www.adio.gov.ae/en/resources")
    assert len(items) >= 1
    names = [i["name"] for i in items]
    assert any("project" in n.lower() or "ppp" in n.lower() for n in names)


@pytest.mark.asyncio
async def test_adio_scraper_required_fields():
    from backend.scrapers.adio import ADIOScraper

    scraper = ADIOScraper()
    items = scraper._parse_listing(ADIO_SAMPLE_HTML, "https://www.adio.gov.ae")
    for item in items:
        assert "name" in item
        assert "url" in item
        assert "raw_text" in item
        assert "source_name" in item


@pytest.mark.asyncio
async def test_news_scraper_filters_ppp():
    from backend.scrapers.news import NewsScraper
    import feedparser

    scraper = NewsScraper()
    feed = feedparser.parse(NEWS_SAMPLE_RSS)

    with patch.object(scraper, "fetch", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = NEWS_SAMPLE_RSS
        with patch("feedparser.parse", return_value=feed):
            with patch.object(scraper, "rate_limit", new_callable=AsyncMock):
                results = await scraper.scrape()

    assert isinstance(results, list)
    titles = [r["name"] for r in results]
    assert any("etihad" in t.lower() or "billion" in t.lower() for t in titles)
    assert not any("restaurant" in t.lower() for t in titles)


@pytest.mark.asyncio
async def test_base_scraper_fetch_retries_on_error():
    from backend.scrapers.wam import WAMScraper
    import httpx

    scraper = WAMScraper()
    scraper.max_retries = 2

    call_count = 0

    async def mock_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise httpx.RequestError("timeout")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "success"
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    async with httpx.AsyncClient() as client:
        with patch.object(client, "get", side_effect=mock_get):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await scraper.fetch("https://example.com", client)

    assert result == "success"
    assert call_count == 2
