from __future__ import annotations
from google import genai
from backend.config import settings
from backend.utils.logging import get_logger

logger = get_logger(__name__)

BLOCKED_RESPONSE = (
    "I can only assist with UAE PPP and infrastructure project queries. "
    "Please ask me about UAE projects, sectors, contractors, or procurement."
)

GUARDRAIL_PROMPT = """You are a guardrail classifier for a UAE PPP (Public-Private Partnership) intelligence portal.

Classify whether the following user query is about UAE infrastructure or PPP projects.

Allowed topics: UAE PPP projects, UAE infrastructure, UAE government contracts, UAE construction, UAE energy,
UAE transport, UAE water, UAE healthcare, UAE education, UAE tenders, UAE contractors, UAE airports, UAE ports,
UAE roads, UAE metro, UAE solar, UAE nuclear, UAE desalination projects.

Query: {query}

Respond with exactly one word: "allowed" or "blocked"."""


class GuardrailChecker:
    """Checks if a query is in-domain for UAE PPP topics."""

    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    async def is_in_domain(self, query: str) -> bool:
        """Return True if query is about UAE PPP/infrastructure, False otherwise."""
        query_lower = query.lower()
        allowed_keywords = [
            "uae", "dubai", "abu dhabi", "sharjah", "emirates", "emirati",
            "project", "ppp", "infrastructure", "contract", "tender", "billion",
            "contractor", "sector", "transport", "energy", "water", "healthcare",
            "education", "solar", "metro", "airport", "port", "hospital", "school",
            "power", "desalination", "railway", "road", "construction",
        ]
        blocked_keywords = [
            "weather", "recipe", "sport", "football", "cricket", "movie", "music",
            "celebrity", "politics", "election", "covid", "diet", "fashion",
            "travel guide", "restaurant", "joke", "story", "game",
        ]
        has_allowed = any(kw in query_lower for kw in allowed_keywords)
        has_blocked = any(kw in query_lower for kw in blocked_keywords)

        if has_blocked and not has_allowed:
            return False
        if has_allowed:
            return True

        try:
            prompt = GUARDRAIL_PROMPT.format(query=query)
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            result = response.text.strip().lower()
            return "allowed" in result
        except Exception as e:
            logger.warning("guardrail_api_error", error=str(e))
            return True
