from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from backend.db.session import get_db
from backend.db import crud

router = APIRouter(prefix="/api", tags=["projects"])


class ProjectOut(BaseModel):
    id: int
    name: str
    sector: str
    emirate: str
    owner: str
    contract_value_aed: Optional[float]
    status: str
    contractors: Optional[str]
    expected_completion_year: Optional[int]
    source_url: str
    source_name: str
    extraction_confidence: float
    notes: Optional[str]

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    projects: list[ProjectOut]
    total: int
    skip: int
    limit: int


class StatsResponse(BaseModel):
    total_projects: int
    total_value_aed_billions: float
    by_sector: dict
    by_emirate: dict
    by_status: dict


@router.get("/projects", response_model=ProjectListResponse)
async def list_projects(
    sector: Optional[str] = Query(None),
    emirate: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    min_value: Optional[float] = Query(None),
    max_value: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> ProjectListResponse:
    projects, total = await crud.get_projects(
        session=db,
        sector=sector,
        emirate=emirate,
        status=status,
        min_value=min_value,
        max_value=max_value,
        search=search,
        skip=skip,
        limit=limit,
    )
    return ProjectListResponse(
        projects=[ProjectOut.model_validate(p) for p in projects],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)) -> StatsResponse:
    stats = await crud.get_stats(db)
    return StatsResponse(**stats)
