from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.db.session import get_db


async def _mock_db():
    """Mock DB session for API tests."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from backend.db.models import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        from backend.db.crud import create_project
        await create_project(session, {
            "name": "Dubai Metro Blue Line",
            "sector": "Transport",
            "emirate": "Dubai",
            "owner": "RTA",
            "contract_value_aed": 30.0,
            "status": "Under Execution",
            "source_url": "https://rta.ae",
            "source_name": "RTA Dubai",
        })
        await create_project(session, {
            "name": "Al Dhafra Solar PV",
            "sector": "Energy",
            "emirate": "Abu Dhabi",
            "owner": "ADPower",
            "contract_value_aed": 5.5,
            "status": "Complete",
            "source_url": "https://adpower.ae",
            "source_name": "ADPower",
        })
        await session.commit()
        yield session
    await engine.dispose()


@pytest.fixture
def client_with_db():
    app.dependency_overrides[get_db] = _mock_db
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_endpoint(client_with_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "db_status" in data
    assert "project_count" in data


@pytest.mark.asyncio
async def test_projects_list(client_with_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/projects")
    assert response.status_code == 200
    data = response.json()
    assert "projects" in data
    assert "total" in data
    assert data["total"] >= 2


@pytest.mark.asyncio
async def test_projects_filter_by_sector(client_with_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/projects?sector=Transport")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["projects"][0]["sector"] == "Transport"


@pytest.mark.asyncio
async def test_projects_filter_by_emirate(client_with_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/projects?emirate=Dubai")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["projects"][0]["emirate"] == "Dubai"


@pytest.mark.asyncio
async def test_projects_filter_by_min_value(client_with_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/projects?min_value=10")
    assert response.status_code == 200
    data = response.json()
    assert all(p["contract_value_aed"] >= 10.0 for p in data["projects"] if p["contract_value_aed"])


@pytest.mark.asyncio
async def test_stats_endpoint(client_with_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_projects" in data
    assert "total_value_aed_billions" in data
    assert "by_sector" in data
    assert "by_emirate" in data
    assert "by_status" in data


@pytest.mark.asyncio
async def test_chat_endpoint_with_domain_query(client_with_db):
    mock_result = {
        "reply": "I found 1 transport project in Dubai: Dubai Metro Blue Line.",
        "in_domain": True,
        "filters_applied": {"sector": "Transport", "emirate": "Dubai"},
        "result_count": 1,
        "projects": [{"name": "Dubai Metro Blue Line", "sector": "Transport"}],
    }
    with patch("backend.agents.ppp_agent.PPPAgent.run", new_callable=AsyncMock, return_value=mock_result):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/chat", json={"message": "Show me transport projects in Dubai"})
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "session_id" in data
    assert "result_count" in data


@pytest.mark.asyncio
async def test_chat_endpoint_generates_session_id(client_with_db):
    mock_result = {
        "reply": "Here are the projects.",
        "in_domain": True,
        "filters_applied": {},
        "result_count": 0,
        "projects": [],
    }
    with patch("backend.agents.ppp_agent.PPPAgent.run", new_callable=AsyncMock, return_value=mock_result):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/chat", json={"message": "Hello"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["session_id"]) > 0


@pytest.mark.asyncio
async def test_root_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "UAE PPP" in data["message"]
