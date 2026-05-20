import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.models.chat import ChatEvent, ChatSession


async def upsert_session(
    session: AsyncSession,
    *,
    session_key: str,
    user_agent: str | None,
    ip_hash: str | None,
) -> ChatSession:
    stmt = select(ChatSession).where(ChatSession.session_key == session_key)
    chat_session = (await session.execute(stmt)).scalars().first()
    if chat_session is None:
        chat_session = ChatSession(
            session_key=session_key,
            user_agent=user_agent,
            ip_hash=ip_hash,
            message_count=0,
        )
        session.add(chat_session)
        await session.flush()
        await session.refresh(chat_session)
        return chat_session

    chat_session.message_count = (chat_session.message_count or 0) + 1
    chat_session.last_message_at = func.now()
    if user_agent and not chat_session.user_agent:
        chat_session.user_agent = user_agent
    if ip_hash and not chat_session.ip_hash:
        chat_session.ip_hash = ip_hash
    await session.flush()
    return chat_session


async def log_event(
    session: AsyncSession,
    *,
    session_id: uuid.UUID,
    agent_used: str,
    latency_ms: int,
    tokens_in: int,
    tokens_out: int,
    tool_calls_count: int,
    error: str | None = None,
) -> ChatEvent:
    event = ChatEvent(
        session_id=session_id,
        agent_used=agent_used,
        latency_ms=latency_ms,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        tool_calls_count=tool_calls_count,
        error=error,
    )
    session.add(event)
    await session.flush()
    return event
