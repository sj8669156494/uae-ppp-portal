from __future__ import annotations
import json
import re
from typing import Optional
from google import genai
from backend.config import settings
from backend.utils.logging import get_logger

logger = get_logger(__name__)

VALID_SECTORS = {"Transport", "Energy", "Water", "Healthcare", "Education", "Social", "Infrastructure", "Environment", "Other"}
VALID_EMIRATES = {"Abu Dhabi", "Dubai", "Sharjah", "Ras Al Khaimah", "Fujairah", "Ajman", "Umm Al Quwain", "Multiple", "Federal"}
VALID_STATUSES = {"Planned", "Tendering", "Under Execution", "Complete"}

EXTRACTION_PROMPT = """You are a UAE infrastructure and PPP (Public-Private Partnership) project data extractor.

Extract structured information from the following text about a UAE infrastructure or PPP project.

Return ONLY a valid JSON object with these exact fields:
{{
  "name": "Full project name (string, required)",
  "sector": "One of: Transport, Energy, Water, Healthcare, Education, Social, Infrastructure, Environment, Other",
  "emirate": "One of: Abu Dhabi, Dubai, Sharjah, Ras Al Khaimah, Fujairah, Ajman, Umm Al Quwain, Multiple, Federal",
  "owner": "Government entity or client (string, required)",
  "contract_value_aed": "Contract value in AED billions as a float (e.g., 5.0 for AED 5 billion), or null if unknown",
  "status": "One of: Planned, Tendering, Under Execution, Complete",
  "contractors": "Main contractor(s) as a string, or null if unknown",
  "expected_completion_year": "Year as integer (e.g., 2026), or null if unknown",
  "confidence": "Your confidence in this extraction from 0.0 to 1.0"
}}

Rules:
- Convert all monetary values to AED billions (1 billion USD ≈ 3.67 AED billion)
- For status: look for keywords — "planned"→Planned, "tender/RFP/bid"→Tendering, "under construction/awarded/executing"→Under Execution, "complete/operational/opened"→Complete
- If uncertain about emirate, use "Multiple" for federal projects or cross-emirate projects
- Return ONLY valid JSON — no explanations, no markdown

Text to extract from:
{text}"""


class ProjectExtractor:
    """Extracts structured UAE PPP project data from raw text using Gemini."""

    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    async def extract(self, raw_text: str, source_url: str) -> Optional[dict]:
        """Extract project data from raw text. Returns dict or None if extraction fails."""
        if len(raw_text.strip()) < 20:
            return None

        truncated = raw_text[:4000]
        prompt = EXTRACTION_PROMPT.format(text=truncated)

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            content = response.text.strip()
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
            data = json.loads(content)
            return self._validate_and_enrich(data, raw_text, source_url)
        except json.JSONDecodeError as e:
            logger.warning("extraction_json_error", error=str(e), url=source_url)
            return None
        except Exception as e:
            logger.error("extraction_error", error=str(e), url=source_url)
            return None

    def _validate_and_enrich(self, data: dict, raw_text: str, source_url: str) -> Optional[dict]:
        name = data.get("name", "").strip()
        if not name or len(name) < 5:
            return None

        sector = data.get("sector", "Other")
        if sector not in VALID_SECTORS:
            sector = "Other"

        emirate = data.get("emirate", "Multiple")
        if emirate not in VALID_EMIRATES:
            emirate = "Multiple"

        status = data.get("status", "Planned")
        if status not in VALID_STATUSES:
            status = "Planned"

        confidence = float(data.get("confidence", 0.7))
        confidence = max(0.0, min(1.0, confidence))

        contract_value = data.get("contract_value_aed")
        if contract_value is not None:
            try:
                contract_value = float(contract_value)
            except (TypeError, ValueError):
                contract_value = None

        year = data.get("expected_completion_year")
        if year is not None:
            try:
                year = int(year)
                if year < 2000 or year > 2050:
                    year = None
            except (TypeError, ValueError):
                year = None

        return {
            "name": name[:500],
            "sector": sector,
            "emirate": emirate,
            "owner": str(data.get("owner", "Unknown"))[:500],
            "contract_value_aed": contract_value,
            "status": status,
            "contractors": str(data.get("contractors", ""))[:1000] if data.get("contractors") else None,
            "expected_completion_year": year,
            "source_url": source_url,
            "source_name": "Scraped",
            "raw_text": raw_text[:10000],
            "extraction_confidence": confidence,
        }
