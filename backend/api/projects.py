from __future__ import annotations
import csv
import io
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
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
    # V2 extended fields
    description: Optional[str] = None
    sub_sector: Optional[str] = None
    responsible_entity: Optional[str] = None
    project_type: Optional[str] = None
    mode_of_implementation: Optional[str] = None
    ppp_type: Optional[str] = None
    ppp_model: Optional[str] = None
    requirements: Optional[str] = None
    start_date: Optional[str] = None
    tender_end_date: Optional[str] = None
    news_link: Optional[str] = None
    ministry_link: Optional[str] = None
    contact_details: Optional[str] = None

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


@router.get("/projects/export.csv")
async def export_projects_csv(
    sector: Optional[str] = Query(None),
    emirate: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Download all matching projects as a CSV file."""
    projects, _ = await crud.get_projects(
        session=db, sector=sector, emirate=emirate, status=status, limit=1000
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "name", "sector", "sub_sector", "emirate", "owner",
        "responsible_entity", "contract_value_aed_billions", "status",
        "contractors", "expected_completion_year", "project_type",
        "mode_of_implementation", "ppp_type", "ppp_model",
        "start_date", "tender_end_date", "source_url", "source_name",
        "news_link", "ministry_link", "contact_details",
        "extraction_confidence", "notes", "description",
    ])
    for p in projects:
        writer.writerow([
            p.id, p.name, p.sector, p.sub_sector, p.emirate, p.owner,
            p.responsible_entity, p.contract_value_aed, p.status,
            p.contractors, p.expected_completion_year, p.project_type,
            p.mode_of_implementation, p.ppp_type, p.ppp_model,
            p.start_date, p.tender_end_date, p.source_url, p.source_name,
            p.news_link, p.ministry_link, p.contact_details,
            p.extraction_confidence, p.notes, p.description,
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=uae_ppp_projects.csv"},
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)) -> StatsResponse:
    stats = await crud.get_stats(db)
    return StatsResponse(**stats)
