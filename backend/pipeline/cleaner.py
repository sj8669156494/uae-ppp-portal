from __future__ import annotations
import re
from typing import Optional
from rapidfuzz import fuzz
from backend.utils.logging import get_logger

logger = get_logger(__name__)

VALUE_PATTERNS = [
    (r"AED\s*([\d,.]+)\s*billion", 1.0, "AED_billion"),
    (r"AED\s*([\d,.]+)\s*bn", 1.0, "AED_billion"),
    (r"Dh\s*([\d,.]+)\s*billion", 1.0, "AED_billion"),
    (r"Dh\s*([\d,.]+)\s*bn", 1.0, "AED_billion"),
    (r"\bAED\s*([\d,.]+)\s*million", 0.001, "AED_million"),
    (r"\$([\d,.]+)\s*billion", 3.67, "USD_billion"),
    (r"\$([\d,.]+)\s*bn", 3.67, "USD_billion"),
    (r"\$([\d,.]+)\s*million", 0.00367, "USD_million"),
    (r"([\d,.]+)\s*billion\s*dirham", 1.0, "AED_billion_2"),
]

EMIRATE_PATTERNS = {
    "Abu Dhabi": ["abu dhabi", "abudhabi", "adnoc", "adec", "doh abu dhabi", "mubadala"],
    "Dubai": ["dubai", "dewa", "rta", "emaar"],
    "Sharjah": ["sharjah", "sewa"],
    "Ras Al Khaimah": ["ras al khaimah", "rak", "ra'as al-khaimah"],
    "Fujairah": ["fujairah"],
    "Ajman": ["ajman"],
    "Umm Al Quwain": ["umm al quwain", "uaq"],
}

DUPLICATION_THRESHOLD = 80


class ProjectCleaner:
    """Cleans, normalises, and deduplicates extracted project data."""

    def clean(self, data: Optional[dict]) -> Optional[dict]:
        if not data:
            return None
        data = dict(data)
        if not data.get("name") or not data.get("sector"):
            return None
        data["name"] = self._clean_text(data.get("name", ""))
        data["owner"] = self._clean_text(data.get("owner", "Unknown"))
        if data.get("raw_text") and not data.get("contract_value_aed"):
            data["contract_value_aed"] = self._extract_value(data["raw_text"])
        if data.get("raw_text") and data.get("emirate") in (None, "Multiple"):
            detected = self._detect_emirate(data["raw_text"])
            if detected:
                data["emirate"] = detected
        data["name"] = data["name"][:500]
        data["owner"] = data["owner"][:500]
        if data.get("contractors"):
            data["contractors"] = data["contractors"][:1000]
        return data

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"[^\w\s\-(),./&'\":]", "", text)
        return text

    def _extract_value(self, text: str) -> Optional[float]:
        for pattern, multiplier, _ in VALUE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    raw = match.group(1).replace(",", "")
                    value = float(raw) * multiplier
                    if 0.001 <= value <= 1000:
                        return round(value, 3)
                except (ValueError, IndexError):
                    continue
        return None

    def _detect_emirate(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for emirate, keywords in EMIRATE_PATTERNS.items():
            if any(kw in text_lower for kw in keywords):
                return emirate
        return None

    def is_duplicate(self, name1: str, name2: str) -> bool:
        n1, n2 = name1.lower(), name2.lower()
        ratio = max(
            fuzz.token_sort_ratio(n1, n2),
            fuzz.partial_ratio(n1, n2),
        )
        return ratio >= DUPLICATION_THRESHOLD

    def find_duplicate(self, candidate_name: str, existing_names: list[str]) -> Optional[str]:
        for name in existing_names:
            if self.is_duplicate(candidate_name, name):
                return name
        return None
