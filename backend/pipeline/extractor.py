from __future__ import annotations
import json
import re
from typing import Optional
from openai import AsyncOpenAI
from backend.config import settings
from backend.utils.logging import get_logger

logger = get_logger(__name__)

VALID_SECTORS = {"Transport", "Energy", "Water", "Healthcare", "Education", "Social", "Infrastructure", "Environment", "Other"}
VALID_EMIRATES = {"Abu Dhabi", "Dubai", "Sharjah", "Ras Al Khaimah", "Fujairah", "Ajman", "Umm Al Quwain", "Multiple", "Federal"}
VALID_STATUSES = {"Planned", "Tendering", "Under Execution", "Complete"}

EXTRACTION_PROMPT = """You are a UAE infrastructure and PPP (Public-Private Partnership) project data extractor.

Extract structured information from the following text about a UAE infrastructure or PPP project.

Return ONLY a valid JSON object with these exact fields:
{
  "name": "Full project name (string, required)",
  "sector": "One of: Transport, Energy, Water, Healthcare, Education, Social, Infrastructure, Environment, Other",
  "emirate": "One of: Abu Dhabi, Dubai, Sharjah, Ras Al Khaimah, Fujairah, Ajman, Umm Al Quwain, Multiple, Federal",
  "owner": "Government entity or client (string, required)",
  "contract_value_aed": "Contract value in AED billions as a float (e.g., 5.0 for AED 5 billion), or null if unknown",
  "status": "One of: Planned, Tendering, Under Execution, Complete",
  "contractors": "Main contractor(s) as a string, or null if unknown",
  "expected_completion_year": "Year as integer (e.g., 2026), or null if unknown",
  "description": "Brief description of the project scope and objectives, or null",
  "sub_sector": "Specific sub-category (e.g. Road, Rail, Airport, Solar, Nuclear, Hospital), or null",
  "responsible_entity": "Government ministry or authority directly responsible for oversight, or null",
  "project_type": "One of: Greenfield, Brownfield, Expansion, Rehabilitation, or null",
  "mode_of_implementation": "How it is delivered (e.g. Design-Build, DBOM, DBFOM, EPC, O&M), or null",
  "ppp_type": "Type of PPP arrangement (e.g. Concession, Joint Venture, Availability Payment, Service Contract), or null",
  "ppp_model": "PPP financial model (e.g. BOT, BOOT, BTO, DBFOT, Lease, O&M), or null",
  "requirements": "Key technical or legal requirements mentioned, or null",
  "start_date": "Project start date as YYYY-MM-DD, or null",
  "tender_end_date": "Tender submission deadline as YYYY-MM-DD, or null",
  "news_link": "URL to a relevant news article if mentioned in text, or null",
  "ministry_link": "URL to the official ministry or department page if mentioned, or null",
  "contact_details": "Contact name, email or phone if mentioned, or null",
  "confidence": "Your confidence in this extraction from 0.0 to 1.0"
}

Rules:
- Convert all monetary values to AED billions (1 billion USD ≈ 3.67 AED billion)
- For status: look for keywords — "planned"→Planned, "tender/RFP/bid"→Tendering, "under construction/awarded/executing"→Under Execution, "complete/operational/opened"→Complete
- If uncertain about emirate, use "Multiple" for federal/cross-emirate projects
- Only extract URLs actually present in the text — do not fabricate links
- Return ONLY valid JSON — no explanations, no markdown"""


class ProjectExtractor:
    """Extracts structured UAE PPP project data from raw text using OpenAI."""

    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def extract(self, raw_text: str, source_url: str) -> Optional[dict]:
        """Extract project data from raw text. Returns dict or None if extraction fails."""
        if len(raw_text.strip()) < 20:
            return None

        truncated = raw_text[:4000]

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": EXTRACTION_PROMPT},
                    {"role": "user", "content": f"Text to extract from:\n{truncated}"},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or ""
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

        def _safe_str(key: str, max_len: int) -> Optional[str]:
            val = data.get(key)
            return str(val)[:max_len] if val else None

        def _safe_url(key: str) -> Optional[str]:
            val = data.get(key)
            if not val:
                return None
            s = str(val).strip()
            return s[:2000] if s.startswith("http") else None

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
            # V2 extended fields
            "description": _safe_str("description", 5000),
            "sub_sector": _safe_str("sub_sector", 200),
            "responsible_entity": _safe_str("responsible_entity", 500),
            "project_type": _safe_str("project_type", 200),
            "mode_of_implementation": _safe_str("mode_of_implementation", 200),
            "ppp_type": _safe_str("ppp_type", 200),
            "ppp_model": _safe_str("ppp_model", 200),
            "requirements": _safe_str("requirements", 5000),
            "start_date": _safe_str("start_date", 20),
            "tender_end_date": _safe_str("tender_end_date", 20),
            "news_link": _safe_url("news_link"),
            "ministry_link": _safe_url("ministry_link"),
            "contact_details": _safe_str("contact_details", 1000),
        }
