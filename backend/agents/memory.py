from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ConversationFilters:
    """Active filters accumulated across conversation turns."""
    sector: Optional[str] = None
    emirate: Optional[str] = None
    status: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in {
            "sector": self.sector,
            "emirate": self.emirate,
            "status": self.status,
            "min_value": self.min_value,
            "max_value": self.max_value,
        }.items() if v is not None}

    def update(self, new_filters: dict) -> None:
        """Merge new filters into current state (additive, not replacing)."""
        if "sector" in new_filters and new_filters["sector"]:
            self.sector = new_filters["sector"]
        if "emirate" in new_filters and new_filters["emirate"]:
            self.emirate = new_filters["emirate"]
        if "status" in new_filters and new_filters["status"]:
            self.status = new_filters["status"]
        if "min_value" in new_filters and new_filters["min_value"] is not None:
            self.min_value = new_filters["min_value"]
        if "max_value" in new_filters and new_filters["max_value"] is not None:
            self.max_value = new_filters["max_value"]

    def reset(self) -> None:
        self.sector = None
        self.emirate = None
        self.status = None
        self.min_value = None
        self.max_value = None


@dataclass
class SessionMemory:
    """Tracks conversation state across turns within a session."""
    session_id: str
    active_filters: ConversationFilters = field(default_factory=ConversationFilters)
    query_history: list[str] = field(default_factory=list)
    result_count: int = 0

    def record_query(self, query: str, result_count: int) -> None:
        self.query_history.append(query)
        self.result_count = result_count
        if len(self.query_history) > 20:
            self.query_history = self.query_history[-20:]


_session_store: dict[str, SessionMemory] = {}


def get_or_create_session(session_id: str) -> SessionMemory:
    if session_id not in _session_store:
        _session_store[session_id] = SessionMemory(session_id=session_id)
    return _session_store[session_id]


def clear_session(session_id: str) -> None:
    _session_store.pop(session_id, None)
