from __future__ import annotations
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.db.session import init_db
from backend.utils.logging import setup_logging, get_logger
from backend.api import health, projects, chat
from backend.pipeline.scheduler import start_scheduler, stop_scheduler

logger = get_logger(__name__)


async def _seed_if_empty() -> None:
    """Auto-seed the DB with known projects if empty (for fresh production deployments)."""
    from backend.db.session import AsyncSessionLocal
    from backend.db.crud import get_stats, upsert_project
    from scripts.seed_db import SEED_PROJECTS
    async with AsyncSessionLocal() as session:
        stats = await get_stats(session)
        if stats["total_projects"] == 0:
            logger.info("seeding_empty_database")
            for project_data in SEED_PROJECTS:
                await upsert_project(session, project_data)
            await session.commit()
            logger.info("seeding_complete", count=len(SEED_PROJECTS))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    logger.info("startup", env=settings.app_env)
    await init_db()
    await _seed_if_empty()
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("shutdown")


app = FastAPI(
    title="UAE PPP Intelligence Portal",
    description="AI-powered UAE Public-Private Partnership project intelligence platform",
    version="1.0.0",
    lifespan=lifespan,
)

_origins = [settings.frontend_url, "http://localhost:5173", "http://localhost:3000"]
if settings.app_env == "production":
    _origins.append("https://*.onrender.com")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(projects.router)
app.include_router(chat.router)


@app.get("/")
async def root() -> dict:
    return {"message": "UAE PPP Intelligence Portal API", "docs": "/docs"}
