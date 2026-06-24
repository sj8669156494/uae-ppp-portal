from __future__ import annotations
import json
import re
from google import genai
from sqlalchemy.ext.asyncio import AsyncSession
from backend.config import settings
from backend.agents.guardrails import GuardrailChecker, BLOCKED_RESPONSE
from backend.agents.memory import get_or_create_session, ConversationFilters
from backend.db import crud
from backend.utils.logging import get_logger

logger = get_logger(__name__)

VALID_SECTORS = {"Transport", "Energy", "Water", "Healthcare", "Education", "Social", "Infrastructure", "Environment", "Other"}
VALID_EMIRATES = {"Abu Dhabi", "Dubai", "Sharjah", "Ras Al Khaimah", "Fujairah", "Ajman", "Umm Al Quwain", "Multiple", "Federal"}
VALID_STATUSES = {"Planned", "Tendering", "Under Execution", "Complete"}

FILTER_EXTRACTION_PROMPT = """Extract search filters from this UAE PPP project query.

Return ONLY a JSON object with these optional fields:
{{
  "sector": "One of: Transport, Energy, Water, Healthcare, Education, Social, Infrastructure, Environment, Other — or null",
  "emirate": "One of: Abu Dhabi, Dubai, Sharjah, Ras Al Khaimah, Fujairah, Ajman, Umm Al Quwain, Multiple, Federal — or null",
  "status": "One of: Planned, Tendering, Under Execution, Complete — or null",
  "min_value": "Minimum contract value in AED billions as float — or null",
  "max_value": "Maximum contract value in AED billions as float — or null",
  "reset_filters": "true if user explicitly wants to start a new search — or false"
}}

Context from previous turn (current active filters): {current_filters}

User query: {query}

Rules:
- "now only X" or "just show X" → add X to existing filters
- "start over" or "reset" → set reset_filters to true
- "above AED 10 billion" → min_value: 10.0
- "road projects" → sector: Transport
- "water projects still in tendering" → sector: Water, status: Tendering
- Return ONLY valid JSON"""

RESPONSE_PROMPT = """You are an assistant for a UAE PPP Intelligence Portal.

User asked: {query}

Active filters: {filters}

Results found: {count} projects
Top results:
{results_summary}

Write a concise, professional response (2-4 sentences) summarising what was found.
Mention the sector, emirate, and status filters if applied. List 2-3 project names.
If no results found, suggest broadening the search."""


class PPPAgent:
    """Conversational agent for UAE PPP project queries, powered by Gemini."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.guardrail = GuardrailChecker()
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    async def run(self, message: str, session_id: str) -> dict:
        """Process a user message and return response with projects."""
        memory = get_or_create_session(session_id)

        # Step 1: Guardrail check
        in_domain = await self.guardrail.is_in_domain(message)
        if not in_domain:
            return {
                "reply": BLOCKED_RESPONSE,
                "in_domain": False,
                "filters_applied": {},
                "result_count": 0,
                "projects": [],
            }

        # Step 2: Extract filters from message
        new_filters = await self._extract_filters(message, memory.active_filters)

        if new_filters.get("reset_filters"):
            memory.active_filters.reset()

        memory.active_filters.update(new_filters)
        active = memory.active_filters.to_dict()

        # Step 3: Query database
        projects, total = await crud.get_projects(
            session=self.db,
            sector=active.get("sector"),
            emirate=active.get("emirate"),
            status=active.get("status"),
            min_value=active.get("min_value"),
            max_value=active.get("max_value"),
            limit=20,
        )

        memory.record_query(message, total)

        # Step 4: Format response
        results_summary = self._format_results(projects[:5])
        reply = await self._generate_reply(message, active, total, results_summary)

        project_dicts = [
            {
                "id": p.id,
                "name": p.name,
                "sector": p.sector,
                "emirate": p.emirate,
                "owner": p.owner,
                "contract_value_aed": p.contract_value_aed,
                "status": p.status,
                "contractors": p.contractors,
                "expected_completion_year": p.expected_completion_year,
            }
            for p in projects[:10]
        ]

        return {
            "reply": reply,
            "in_domain": True,
            "filters_applied": active,
            "result_count": total,
            "projects": project_dicts,
        }

    async def _extract_filters(self, query: str, current_filters: ConversationFilters) -> dict:
        """Use Gemini to extract structured filters from the user query."""
        prompt = FILTER_EXTRACTION_PROMPT.format(
            current_filters=json.dumps(current_filters.to_dict()),
            query=query,
        )
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            content = response.text.strip()
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
            data = json.loads(content)
            result: dict = {}
            if data.get("sector") in VALID_SECTORS:
                result["sector"] = data["sector"]
            if data.get("emirate") in VALID_EMIRATES:
                result["emirate"] = data["emirate"]
            if data.get("status") in VALID_STATUSES:
                result["status"] = data["status"]
            if data.get("min_value") is not None:
                try:
                    result["min_value"] = float(data["min_value"])
                except (TypeError, ValueError):
                    pass
            if data.get("max_value") is not None:
                try:
                    result["max_value"] = float(data["max_value"])
                except (TypeError, ValueError):
                    pass
            result["reset_filters"] = bool(data.get("reset_filters", False))
            return result
        except Exception as e:
            logger.warning("filter_extraction_error", error=str(e), query=query)
            return {}

    def _format_results(self, projects: list) -> str:
        if not projects:
            return "No matching projects found."
        lines: list[str] = []
        for p in projects:
            value = f"AED {p.contract_value_aed:.1f}B" if p.contract_value_aed else "value unknown"
            lines.append(f"- {p.name} ({p.emirate}, {p.sector}, {p.status}, {value})")
        return "\n".join(lines)

    async def _generate_reply(self, query: str, filters: dict, count: int, results_summary: str) -> str:
        prompt = RESPONSE_PROMPT.format(
            query=query,
            filters=json.dumps(filters),
            count=count,
            results_summary=results_summary,
        )
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            logger.warning("reply_generation_error", error=str(e))
            if count == 0:
                return "No projects found matching your criteria. Try broadening your search."
            return f"Found {count} project(s) matching your query."
