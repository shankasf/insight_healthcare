import time
from dataclasses import dataclass
from typing import Any

from agents import Runner
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.triage import build_triage_agent
from app.core.logging import get_logger
from app.repositories import chat_repo
from app.schemas.chat import AgentName
from app.services.session_memory import memory as session_memory

logger = get_logger(__name__)

_VALID_AGENT_NAMES: set[AgentName] = {
    "triage",
    "appointment",
    "insurance",
    "knowledge",
    "out_of_scope",
}

_OUT_OF_SCOPE_MARKERS = (
    "i can only help with appointments, insurance acceptance, or info about insight healthcare",
)


@dataclass(slots=True)
class ChatOutcome:
    reply: str
    agent_used: AgentName
    tokens_in: int
    tokens_out: int
    tool_calls_count: int
    latency_ms: int
    error: str | None = None


def _classify_agent(last_agent_name: str | None, final_text: str) -> AgentName:
    name = (last_agent_name or "").strip().lower()
    if name in {"appointment", "insurance", "knowledge"}:
        return name  # type: ignore[return-value]
    lowered = (final_text or "").lower()
    if any(marker in lowered for marker in _OUT_OF_SCOPE_MARKERS):
        return "out_of_scope"
    if name == "triage":
        return "triage"
    return "triage"


def _extract_usage(raw_responses: Any) -> tuple[int, int]:
    tokens_in = 0
    tokens_out = 0
    if not raw_responses:
        return tokens_in, tokens_out
    try:
        for r in raw_responses:
            usage = getattr(r, "usage", None)
            if usage is None and isinstance(r, dict):
                usage = r.get("usage")
            if usage is None:
                continue
            ti = getattr(usage, "input_tokens", None)
            to = getattr(usage, "output_tokens", None)
            if ti is None and isinstance(usage, dict):
                ti = usage.get("input_tokens") or usage.get("prompt_tokens")
                to = usage.get("output_tokens") or usage.get("completion_tokens")
            tokens_in += int(ti or 0)
            tokens_out += int(to or 0)
    except Exception as exc:  # pragma: no cover — telemetry must never break the reply
        logger.warning("usage extraction failed: %s", exc)
    return tokens_in, tokens_out


def _count_tool_calls(new_items: Any) -> int:
    if not new_items:
        return 0
    count = 0
    for item in new_items:
        item_type = getattr(item, "type", None)
        if item_type and "tool_call" in str(item_type).lower() and "output" not in str(item_type).lower():
            count += 1
    return count


async def run_chat(
    session: AsyncSession,
    *,
    message: str,
    session_key: str,
    user_agent: str | None,
    ip_hash: str | None,
) -> ChatOutcome:
    chat_session = await chat_repo.upsert_session(
        session,
        session_key=session_key,
        user_agent=user_agent,
        ip_hash=ip_hash,
    )

    triage = build_triage_agent()
    start = time.monotonic()
    error: str | None = None
    reply = ""
    agent_used: AgentName = "out_of_scope"
    tokens_in = 0
    tokens_out = 0
    tool_calls = 0

    try:
        # Build agent input from prior turns (if any) + this user message.
        # First turn for a session passes a bare string; later turns pass the
        # full conversation list so the head agent sees prior handoff context.
        history = session_memory.get(session_key)
        if history:
            agent_input: Any = history + [{"role": "user", "content": message}]
        else:
            agent_input = message

        result = await Runner.run(triage, input=agent_input)
        reply = result.final_output or ""
        last_agent_name = getattr(getattr(result, "last_agent", None), "name", None)
        agent_used = _classify_agent(last_agent_name, reply)
        tokens_in, tokens_out = _extract_usage(getattr(result, "raw_responses", None))
        tool_calls = _count_tool_calls(getattr(result, "new_items", None))

        # Persist updated conversation in-memory for the next turn. Never let
        # a memory failure break the user-facing reply.
        try:
            session_memory.put(session_key, result.to_input_list())
        except Exception as mem_exc:  # pragma: no cover
            logger.warning("session_memory.put failed: %s", mem_exc)
    except Exception as exc:
        logger.exception("Runner.run failed")
        error = str(exc)[:500]
        reply = "Sorry — something went wrong on our end. Please try again in a moment."
        agent_used = "out_of_scope"

    latency_ms = int((time.monotonic() - start) * 1000)

    await chat_repo.log_event(
        session,
        session_id=chat_session.id,
        agent_used=agent_used,
        latency_ms=latency_ms,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        tool_calls_count=tool_calls,
        error=error,
    )

    return ChatOutcome(
        reply=reply,
        agent_used=agent_used,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        tool_calls_count=tool_calls,
        latency_ms=latency_ms,
        error=error,
    )
