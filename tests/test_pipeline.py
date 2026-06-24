from __future__ import annotations
import pytest
from unittest.mock import MagicMock
from backend.pipeline.cleaner import ProjectCleaner
from backend.pipeline.extractor import ProjectExtractor


# ── Cleaner tests ──────────────────────────────────────────────────────────────

def test_cleaner_normalises_valid_project():
    cleaner = ProjectCleaner()
    data = {
        "name": "Dubai Metro  Blue   Line",
        "sector": "Transport",
        "emirate": "Dubai",
        "owner": "RTA",
        "status": "Under Execution",
        "source_url": "https://rta.ae",
        "source_name": "RTA",
    }
    result = cleaner.clean(data)
    assert result is not None
    assert "Dubai Metro Blue Line" == result["name"]


def test_cleaner_rejects_missing_name():
    cleaner = ProjectCleaner()
    result = cleaner.clean({"sector": "Transport", "emirate": "Dubai", "owner": "RTA", "status": "Planned", "source_url": "x", "source_name": "y"})
    assert result is None


def test_cleaner_rejects_missing_sector():
    cleaner = ProjectCleaner()
    result = cleaner.clean({"name": "Project X", "emirate": "Dubai", "owner": "RTA", "status": "Planned", "source_url": "x", "source_name": "y"})
    assert result is None


def test_cleaner_extracts_aed_billion_value():
    cleaner = ProjectCleaner()
    data = {
        "name": "Power Plant",
        "sector": "Energy",
        "emirate": "Dubai",
        "owner": "DEWA",
        "status": "Planned",
        "source_url": "https://dewa.ae",
        "source_name": "DEWA",
        "raw_text": "The project is valued at AED 5 billion and will be completed by 2027.",
    }
    result = cleaner.clean(data)
    assert result is not None
    assert result["contract_value_aed"] == 5.0


def test_cleaner_extracts_usd_billion_value():
    cleaner = ProjectCleaner()
    data = {
        "name": "Solar Project",
        "sector": "Energy",
        "emirate": "Abu Dhabi",
        "owner": "ADPower",
        "status": "Tendering",
        "source_url": "https://adpower.ae",
        "source_name": "ADPower",
        "raw_text": "Contract worth $2 billion for the solar project",
    }
    result = cleaner.clean(data)
    assert result is not None
    assert result["contract_value_aed"] == pytest.approx(7.34, abs=0.1)


def test_cleaner_extracts_dh_billion_value():
    cleaner = ProjectCleaner()
    data = {
        "name": "Hospital",
        "sector": "Healthcare",
        "emirate": "Abu Dhabi",
        "owner": "DOH",
        "status": "Planned",
        "source_url": "https://doh.ae",
        "source_name": "DOH",
        "raw_text": "Construction costs of Dh3.5 billion approved for the new hospital",
    }
    result = cleaner.clean(data)
    assert result is not None
    assert result["contract_value_aed"] == 3.5


def test_cleaner_detects_emirate_from_text():
    cleaner = ProjectCleaner()
    data = {
        "name": "Water Treatment Plant",
        "sector": "Water",
        "emirate": "Multiple",
        "owner": "SEWA",
        "status": "Tendering",
        "source_url": "https://sewa.ae",
        "source_name": "SEWA",
        "raw_text": "The project is located in Sharjah and will serve industrial areas.",
    }
    result = cleaner.clean(data)
    assert result is not None
    assert result["emirate"] == "Sharjah"


def test_cleaner_duplicate_detection():
    cleaner = ProjectCleaner()
    assert cleaner.is_duplicate("Dubai Metro Blue Line", "Dubai Metro Blue Line Extension") is True
    assert cleaner.is_duplicate("Etihad Rail Project", "Dubai Hospital PPP") is False


def test_cleaner_find_duplicate():
    cleaner = ProjectCleaner()
    existing = ["Etihad Rail Network", "Barakah Nuclear Plant", "Al Dhafra Solar"]
    assert cleaner.find_duplicate("Etihad Rail Network Phase 2", existing) == "Etihad Rail Network"
    assert cleaner.find_duplicate("DEWA Desalination Plant", existing) is None


# ── Extractor tests ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_extractor_parses_valid_json_response():
    extractor = ProjectExtractor.__new__(ProjectExtractor)

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='''{
        "name": "Dubai Solar Park Phase 5",
        "sector": "Energy",
        "emirate": "Dubai",
        "owner": "DEWA",
        "contract_value_aed": 11.4,
        "status": "Under Execution",
        "contractors": "Masdar, EDF",
        "expected_completion_year": 2026,
        "confidence": 0.95
    }''')]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    extractor.client = mock_client

    result = await extractor.extract(
        "Dubai Solar Park Phase 5, awarded to Masdar for AED 11.4 billion by DEWA",
        "https://dewa.gov.ae",
    )
    assert result is not None
    assert result["name"] == "Dubai Solar Park Phase 5"
    assert result["contract_value_aed"] == 11.4
    assert result["sector"] == "Energy"
    assert result["emirate"] == "Dubai"
    assert result["extraction_confidence"] == 0.95


@pytest.mark.asyncio
async def test_extractor_returns_none_for_empty_text():
    extractor = ProjectExtractor.__new__(ProjectExtractor)
    extractor.client = MagicMock()
    result = await extractor.extract("", "https://example.com")
    assert result is None


@pytest.mark.asyncio
async def test_extractor_handles_invalid_json():
    extractor = ProjectExtractor.__new__(ProjectExtractor)

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="This is not JSON at all")]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    extractor.client = mock_client

    result = await extractor.extract("Some project text here", "https://example.com")
    assert result is None


@pytest.mark.asyncio
async def test_extractor_validates_sector_enum():
    extractor = ProjectExtractor.__new__(ProjectExtractor)

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='''{
        "name": "Some Project",
        "sector": "InvalidSector",
        "emirate": "Dubai",
        "owner": "Government",
        "contract_value_aed": 1.0,
        "status": "Planned",
        "contractors": null,
        "expected_completion_year": null,
        "confidence": 0.6
    }''')]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    extractor.client = mock_client

    result = await extractor.extract("Some project info for a Dubai government infrastructure contract worth AED 1 billion.", "https://example.com")
    assert result is not None
    assert result["sector"] == "Other"


@pytest.mark.asyncio
async def test_pipeline_clean_after_extract():
    extractor = ProjectExtractor.__new__(ProjectExtractor)
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='''{
        "name": "Etihad Rail Phase 2",
        "sector": "Transport",
        "emirate": "Federal",
        "owner": "Etihad Rail",
        "contract_value_aed": 25.0,
        "status": "Under Execution",
        "contractors": "CRCC",
        "expected_completion_year": 2024,
        "confidence": 0.9
    }''')]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    extractor.client = mock_client

    raw_text = "Etihad Rail Phase 2: AED 25 billion contract awarded to CRCC in Federal"
    extracted = await extractor.extract(raw_text, "https://etihadrail.ae")
    assert extracted is not None

    cleaner = ProjectCleaner()
    cleaned = cleaner.clean(extracted)
    assert cleaned is not None
    assert cleaned["name"] == "Etihad Rail Phase 2"
    assert cleaned["contract_value_aed"] == 25.0
