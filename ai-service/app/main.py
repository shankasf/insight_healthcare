import hashlib
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_session
from app.core.logging import configure_logging, get_logger
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import run_chat


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    get_logger(__name__).info("ai-service starting (model=%s)", settings.MODEL_NAME)
    yield


app = FastAPI(title="Insight Healthcare AI Service", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _ip_hash(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    raw_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "")
    return hashlib.sha256(raw_ip.encode("utf-8")).hexdigest() if raw_ip else ""


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> ChatResponse:
    user_agent = request.headers.get("user-agent")
    ip_hash_value = _ip_hash(request)

    async with session.begin():
        outcome = await run_chat(
            session,
            message=body.message,
            session_key=body.session_key,
            user_agent=user_agent,
            ip_hash=ip_hash_value or None,
        )

    return ChatResponse(
        reply=outcome.reply,
        agent_used=outcome.agent_used,
        session_key=body.session_key,
    )
