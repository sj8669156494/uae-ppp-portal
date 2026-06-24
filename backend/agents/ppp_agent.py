from __future__ import annotations
import json
from openai import AsyncOpenAI
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

FILTER_SYSTEM = """You extract search filters from UAE PPP project queries.
Return ONLY a JSON object with these optional fields:
{
  "sector": "One of: Transport, Energy, Water, Healthcare, Education, Social, Infrastructure, Environment, Other — or null",
  "emirate": "One of: Abu Dhabi, Dubai, Sharjah, Ras Al Khaimah, Fujairah, Ajman, Umm Al Quwain, Multiple, Federal — or null",
  "status": "One of: Planned, Tendering, Under Execution, Complete — or null",
  "min_value": "Minimum AED billions as float or null",
  "max_value": "Maximum AED billions as float or null",
  "reset_filters": false
}
Rules: "road projects"→Transport, "above AED 10B"→min_value:10.0, "start over"→reset_filters:true"""

RESPONSE_SYSTEM = """You are an assistant for a UAE PPP Intelligence Portal (like Bloomberg Terminal for UAE infrastructure).
Be concise and professional. 2-4 sentences. Mention filters applied, list 2-3 project names.
If no results found, suggest broadening the search."""


class PPPAgent:
    """Conversational agent for UAE PPP project queries, powered by OpenAI."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.guardrail = GuardrailChecker()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def run(self, message: str, session_id: str) -> dict:
        """Process a user message and return response with projects."""
        memory = get_or_create_session(session_id)

        in_domain = await self.guardrail.is_in_domain(message)
        if not in_domain:
            return {
                "reply": BLOCKED_RESPONSE,
                "in_domain": False,
                "filters_applied": {},
                "result_count": 0,
                "projects": [],
            }

        new_filters = await self._extract_filters(message, memory.active_filters)

        if new_filters.get("reset_filters"):
            memory.active_filters.reset()

        memory.active_filters.update(new_filters)
        active = memory.active_filters.to_dict()

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
        user_msg = f"Current filters: {json.dumps(current_filters.to_dict())}\nQuery: {query}"
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": FILTER_SYSTEM},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content or "{}")
            result: dict = {}
            if data.get("sector") in VALID_SECTORS:
                result["sector"] = data["sector"]
            if data.get("emirate") in VALID_EMIRATES:
                result["emirate"] = data["emirate"]
            if data.get("status") in VALID_STATUSES:
                result["status"] = data["status"]
            for key in ("min_value", "max_value"):
                if data.get(key) is not None:
                    try:
                        result[key] = float(data[key])
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
        user_msg = (
            f"User query: {query}\n"
            f"Filters applied: {json.dumps(filters)}\n"
            f"Total results: {count}\n"
            f"Top projects:\n{results_summary}"
        )
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": RESPONSE_SYSTEM},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.3,
                max_tokens=200,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as e:
            logger.warning("reply_generation_error", error=str(e))
            if count == 0:
                return "No projects found matching your criteria. Try broadening your search."
            return f"Found {count} project(s) matching your query."
