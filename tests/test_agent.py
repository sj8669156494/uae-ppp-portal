from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.agents.guardrails import GuardrailChecker, BLOCKED_RESPONSE
from backend.agents.memory import SessionMemory, ConversationFilters, get_or_create_session, clear_session
from backend.agents.ppp_agent import PPPAgent


# ── Guardrail tests ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_guardrail_allows_uae_ppp_query():
    checker = GuardrailChecker.__new__(GuardrailChecker)
    checker.client = MagicMock()
    result = await checker.is_in_domain("Show me road projects in Dubai")
    assert result is True


@pytest.mark.asyncio
async def test_guardrail_allows_water_projects():
    checker = GuardrailChecker.__new__(GuardrailChecker)
    checker.client = MagicMock()
    result = await checker.is_in_domain("Which water projects are tendering in Abu Dhabi?")
    assert result is True


@pytest.mark.asyncio
async def test_guardrail_blocks_off_topic_sports():
    checker = GuardrailChecker.__new__(GuardrailChecker)
    checker.model = "gemini-2.5-flash-lite"
    mock_response = MagicMock()
    mock_response.text = "blocked"
    checker.client = MagicMock()
    checker.client.models.generate_content.return_value = mock_response
    result = await checker.is_in_domain("Who won the FIFA World Cup?")
    assert result is False


@pytest.mark.asyncio
async def test_guardrail_blocks_recipe_query():
    checker = GuardrailChecker.__new__(GuardrailChecker)
    checker.model = "gemini-2.5-flash-lite"
    mock_response = MagicMock()
    mock_response.text = "blocked"
    checker.client = MagicMock()
    checker.client.models.generate_content.return_value = mock_response
    result = await checker.is_in_domain("What is the best recipe for hummus?")
    assert result is False


# ── Memory tests ───────────────────────────────────────────────────────────────

def test_conversation_filters_update():
    filters = ConversationFilters()
    filters.update({"sector": "Transport", "emirate": "Dubai"})
    assert filters.sector == "Transport"
    assert filters.emirate == "Dubai"
    assert filters.status is None


def test_conversation_filters_accumulate():
    filters = ConversationFilters(sector="Transport", emirate="Dubai")
    filters.update({"status": "Under Execution"})
    assert filters.sector == "Transport"
    assert filters.emirate == "Dubai"
    assert filters.status == "Under Execution"


def test_conversation_filters_to_dict():
    filters = ConversationFilters(sector="Energy", min_value=5.0)
    d = filters.to_dict()
    assert d["sector"] == "Energy"
    assert d["min_value"] == 5.0
    assert "emirate" not in d


def test_conversation_filters_reset():
    filters = ConversationFilters(sector="Transport", emirate="Dubai", status="Planned")
    filters.reset()
    assert filters.sector is None
    assert filters.emirate is None
    assert filters.status is None


def test_session_memory_tracks_queries():
    clear_session("test-session")
    mem = get_or_create_session("test-session")
    mem.record_query("Show road projects in Dubai", 5)
    assert len(mem.query_history) == 1
    assert mem.result_count == 5


def test_session_memory_persists_across_calls():
    clear_session("persist-test")
    mem1 = get_or_create_session("persist-test")
    mem1.active_filters.sector = "Energy"
    mem2 = get_or_create_session("persist-test")
    assert mem2.active_filters.sector == "Energy"


# ── Agent tests ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_agent_blocks_off_topic_query(db_session):
    agent = PPPAgent(db=db_session)

    with patch.object(agent.guardrail, "is_in_domain", new_callable=AsyncMock, return_value=False):
        result = await agent.run("Who won the FIFA World Cup?", "session-001")

    assert result["in_domain"] is False
    assert result["reply"] == BLOCKED_RESPONSE
    assert result["result_count"] == 0
    assert result["projects"] == []


@pytest.mark.asyncio
async def test_agent_returns_projects_for_domain_query(db_session):
    from backend.db.crud import create_project
    await create_project(db_session, {
        "name": "Dubai Metro Blue Line",
        "sector": "Transport",
        "emirate": "Dubai",
        "owner": "RTA",
        "contract_value_aed": 30.0,
        "status": "Under Execution",
        "source_url": "https://rta.ae",
        "source_name": "RTA",
    })

    agent = PPPAgent(db=db_session)

    with patch.object(agent.guardrail, "is_in_domain", new_callable=AsyncMock, return_value=True):
        with patch.object(agent, "_extract_filters", new_callable=AsyncMock, return_value={"sector": "Transport", "emirate": "Dubai"}):
            with patch.object(agent, "_generate_reply", new_callable=AsyncMock, return_value="Found 1 transport project in Dubai."):
                result = await agent.run("Show me road projects in Dubai", "session-002")

    assert result["in_domain"] is True
    assert result["result_count"] == 1
    assert len(result["projects"]) == 1
    assert result["projects"][0]["name"] == "Dubai Metro Blue Line"
    assert result["filters_applied"].get("sector") == "Transport"


@pytest.mark.asyncio
async def test_agent_accumulates_filters_across_turns(db_session):
    from backend.db.crud import create_project
    await create_project(db_session, {
        "name": "Dubai Water Treatment",
        "sector": "Water",
        "emirate": "Dubai",
        "owner": "DEWA",
        "status": "Tendering",
        "contract_value_aed": 2.0,
        "source_url": "https://dewa.ae",
        "source_name": "DEWA",
    })

    session_id = "session-multiturn"
    clear_session(session_id)
    agent = PPPAgent(db=db_session)

    with patch.object(agent.guardrail, "is_in_domain", new_callable=AsyncMock, return_value=True):
        with patch.object(agent, "_extract_filters", new_callable=AsyncMock, return_value={"sector": "Water", "emirate": "Dubai"}):
            with patch.object(agent, "_generate_reply", new_callable=AsyncMock, return_value="Found water projects."):
                result1 = await agent.run("Show water projects in Dubai", session_id)

    assert result1["filters_applied"].get("sector") == "Water"

    with patch.object(agent.guardrail, "is_in_domain", new_callable=AsyncMock, return_value=True):
        with patch.object(agent, "_extract_filters", new_callable=AsyncMock, return_value={"status": "Tendering"}):
            with patch.object(agent, "_generate_reply", new_callable=AsyncMock, return_value="Found tendering water projects."):
                result2 = await agent.run("Now only the ones in tendering", session_id)

    assert result2["filters_applied"].get("sector") == "Water"
    assert result2["filters_applied"].get("status") == "Tendering"


@pytest.mark.asyncio
async def test_agent_reset_filters(db_session):
    session_id = "session-reset"
    clear_session(session_id)
    mem = get_or_create_session(session_id)
    mem.active_filters.sector = "Transport"
    mem.active_filters.emirate = "Dubai"

    agent = PPPAgent(db=db_session)

    with patch.object(agent.guardrail, "is_in_domain", new_callable=AsyncMock, return_value=True):
        with patch.object(agent, "_extract_filters", new_callable=AsyncMock, return_value={"reset_filters": True, "sector": "Energy"}):
            with patch.object(agent, "_generate_reply", new_callable=AsyncMock, return_value="Showing energy projects."):
                result = await agent.run("Start over, show energy projects", session_id)

    assert result["filters_applied"].get("sector") == "Energy"
    assert result["filters_applied"].get("emirate") is None
