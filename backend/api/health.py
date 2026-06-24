from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.db.session import get_db
from backend.db.models import Project
from backend.utils.logging import get_logger

router = APIRouter(prefix="/api", tags=["health"])
logger = get_logger(__name__)

_query_count: int = 0
_error_count: int = 0
_last_scraper_run: str | None = None
_error_threshold: int = 10


def increment_query_count() -> None:
    global _query_count
    _query_count += 1


def increment_error_count() -> None:
    global _error_count
    _error_count += 1
    if _error_count >= _error_threshold:
        logger.error(
            "alert_error_threshold_exceeded",
            error_count=_error_count,
            threshold=_error_threshold,
            message="ERROR ALERT: Too many errors — investigate immediately",
        )


def set_last_scraper_run(ts: str) -> None:
    global _last_scraper_run
    _last_scraper_run = ts


def get_query_count() -> int:
    return _query_count


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
    try:
        result = await db.execute(select(func.count(Project.id)))
        project_count = result.scalar_one()
        db_status = "ok"
    except Exception:
        project_count = 0
        db_status = "error"

    alert = None
    if _error_count >= _error_threshold:
        alert = f"HIGH ERROR RATE: {_error_count} errors logged — check logs immediately"

    return {
        "status": "ok" if not alert else "degraded",
        "db_status": db_status,
        "project_count": project_count,
        "query_count_today": _query_count,
        "error_count": _error_count,
        "last_scraper_run": _last_scraper_run or "never",
        "alert": alert,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
