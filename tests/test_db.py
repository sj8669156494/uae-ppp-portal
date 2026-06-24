from __future__ import annotations
import pytest
from backend.db.crud import create_project, get_projects, get_stats, upsert_project

@pytest.mark.asyncio
async def test_create_project(db_session):
    data = {
        "name": "Test Project",
        "sector": "Transport",
        "emirate": "Dubai",
        "owner": "RTA",
        "contract_value_aed": 5.0,
        "status": "Planned",
        "source_url": "https://example.com",
        "source_name": "Test",
        "extraction_confidence": 0.9,
    }
    project = await create_project(db_session, data)
    assert project.id is not None
    assert project.name == "Test Project"
    assert project.sector == "Transport"
    assert project.emirate == "Dubai"


@pytest.mark.asyncio
async def test_get_projects_empty(db_session):
    projects, total = await get_projects(db_session)
    assert projects == []
    assert total == 0


@pytest.mark.asyncio
async def test_get_projects_with_filter(db_session):
    await create_project(db_session, {
        "name": "Dubai Metro",
        "sector": "Transport",
        "emirate": "Dubai",
        "owner": "RTA",
        "status": "Under Execution",
        "source_url": "https://rta.ae",
        "source_name": "RTA",
    })
    await create_project(db_session, {
        "name": "Abu Dhabi Hospital",
        "sector": "Healthcare",
        "emirate": "Abu Dhabi",
        "owner": "DoH",
        "status": "Planned",
        "source_url": "https://doh.ae",
        "source_name": "DOH",
    })

    transport_projects, count = await get_projects(db_session, sector="Transport")
    assert count == 1
    assert transport_projects[0].name == "Dubai Metro"

    _, count2 = await get_projects(db_session, emirate="Dubai")
    assert count2 == 1


@pytest.mark.asyncio
async def test_get_stats(db_session):
    await create_project(db_session, {
        "name": "Project A",
        "sector": "Energy",
        "emirate": "Abu Dhabi",
        "owner": "ADNOC",
        "contract_value_aed": 10.0,
        "status": "Complete",
        "source_url": "https://adnoc.ae",
        "source_name": "ADNOC",
    })
    stats = await get_stats(db_session)
    assert stats["total_projects"] == 1
    assert stats["total_value_aed_billions"] == 10.0
    assert "Energy" in str(stats["by_sector"])


@pytest.mark.asyncio
async def test_upsert_project_no_duplicate(db_session):
    data = {
        "name": "Unique Project",
        "sector": "Water",
        "emirate": "Sharjah",
        "owner": "SEWA",
        "status": "Tendering",
        "source_url": "https://sewa.ae",
        "source_name": "SEWA",
    }
    project1, created1 = await upsert_project(db_session, data)
    project2, created2 = await upsert_project(db_session, data)
    assert created1 is True
    assert created2 is False
    assert project1.id == project2.id
