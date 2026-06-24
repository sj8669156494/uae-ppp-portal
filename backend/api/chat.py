from __future__ import annotations
import time
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from backend.db.session import get_db
from backend.utils.logging import get_logger
from backend.api.health import increment_query_count, increment_error_count

router = APIRouter(prefix="/api", tags=["chat"])
logger = get_logger(__name__)


class ChatRequest(BaseModel):
    message: str
    session_id: str = ""


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    filters_applied: dict
    result_count: int
    projects: list[dict]


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    from backend.agents.ppp_agent import PPPAgent

    session_id = request.session_id or str(uuid.uuid4())
    start = time.time()

    agent = PPPAgent(db=db)
    try:
        result = await agent.run(message=request.message, session_id=session_id)
    except Exception as e:
        increment_error_count()
        logger.error("chat_error", error=str(e), session_id=session_id)
        raise

    latency_ms = (time.time() - start) * 1000
    increment_query_count()
    logger.info(
        "chat_query",
        session_id=session_id,
        query=request.message,
        in_domain=result.get("in_domain", True),
        filters_applied=result.get("filters_applied", {}),
        result_count=result.get("result_count", 0),
        latency_ms=round(latency_ms, 2),
    )

    return ChatResponse(
        reply=result["reply"],
        session_id=session_id,
        filters_applied=result.get("filters_applied", {}),
        result_count=result.get("result_count", 0),
        projects=result.get("projects", []),
    )
