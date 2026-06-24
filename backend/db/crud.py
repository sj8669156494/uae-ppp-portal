from __future__ import annotations
from typing import Optional, Sequence
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.models import Project


async def create_project(session: AsyncSession, project_data: dict) -> Project:
    project = Project(**project_data)
    session.add(project)
    await session.flush()
    await session.refresh(project)
    return project


async def get_project(session: AsyncSession, project_id: int) -> Optional[Project]:
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    return result.scalar_one_or_none()


async def get_projects(
    session: AsyncSession,
    sector: Optional[str] = None,
    emirate: Optional[str] = None,
    status: Optional[str] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[Sequence[Project], int]:
    filters = [Project.is_duplicate.is_(False)]

    if sector:
        filters.append(Project.sector == sector)
    if emirate:
        filters.append(Project.emirate == emirate)
    if status:
        filters.append(Project.status == status)
    if min_value is not None:
        filters.append(Project.contract_value_aed >= min_value)
    if max_value is not None:
        filters.append(Project.contract_value_aed <= max_value)
    if search:
        filters.append(
            Project.name.ilike(f"%{search}%")
            | Project.owner.ilike(f"%{search}%")
            | Project.contractors.ilike(f"%{search}%")
        )

    where_clause = and_(*filters)

    count_result = await session.execute(
        select(func.count(Project.id)).where(where_clause)
    )
    total = count_result.scalar_one()

    result = await session.execute(
        select(Project)
        .where(where_clause)
        .order_by(Project.contract_value_aed.desc().nulls_last())
        .offset(skip)
        .limit(limit)
    )
    projects = result.scalars().all()
    return projects, total


async def get_stats(session: AsyncSession) -> dict:
    total_result = await session.execute(
        select(func.count(Project.id)).where(Project.is_duplicate.is_(False))
    )
    total = total_result.scalar_one()

    value_result = await session.execute(
        select(func.sum(Project.contract_value_aed)).where(Project.is_duplicate.is_(False))
    )
    total_value = value_result.scalar_one() or 0.0

    by_sector_result = await session.execute(
        select(Project.sector, func.count(Project.id))
        .where(Project.is_duplicate.is_(False))
        .group_by(Project.sector)
    )
    by_sector = {row[0]: row[1] for row in by_sector_result}

    by_emirate_result = await session.execute(
        select(Project.emirate, func.count(Project.id))
        .where(Project.is_duplicate.is_(False))
        .group_by(Project.emirate)
    )
    by_emirate = {row[0]: row[1] for row in by_emirate_result}

    by_status_result = await session.execute(
        select(Project.status, func.count(Project.id))
        .where(Project.is_duplicate.is_(False))
        .group_by(Project.status)
    )
    by_status = {row[0]: row[1] for row in by_status_result}

    return {
        "total_projects": total,
        "total_value_aed_billions": round(total_value, 2),
        "by_sector": by_sector,
        "by_emirate": by_emirate,
        "by_status": by_status,
    }


async def mark_duplicate(session: AsyncSession, project_id: int) -> None:
    project = await get_project(session, project_id)
    if project:
        project.is_duplicate = True


async def upsert_project(session: AsyncSession, project_data: dict) -> tuple[Project, bool]:
    """Insert or skip if name+emirate+sector already exists. Returns (project, created)."""
    existing = await session.execute(
        select(Project).where(
            Project.name == project_data.get("name"),
            Project.emirate == project_data.get("emirate"),
        )
    )
    existing_project = existing.scalar_one_or_none()
    if existing_project:
        return existing_project, False
    project = await create_project(session, project_data)
    return project, True
