from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.db.session import get_db
from backend.db.models import Project

router = APIRouter(prefix="/api", tags=["health"])

_query_count: int = 0


def increment_query_count() -> None:
    global _query_count
    _query_count += 1


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

    return {
        "status": "ok",
        "db_status": db_status,
        "project_count": project_count,
        "query_count_today": get_query_count(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
