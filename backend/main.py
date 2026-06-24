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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    logger.info("startup", env=settings.app_env)
    await init_db()
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
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
