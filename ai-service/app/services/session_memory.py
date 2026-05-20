"""In-process session memory keyed by session_key.

GPT-5 is a reasoning model. Its Responses API requires the full
reasoning chain to be present whenever you replay prior items as
`input` — every assistant message and every function_call must be
paired with its preceding reasoning item, and those items are not
easily round-trippable client-side.

We sidestep all of that by using the SDK's `previous_response_id`
mechanism: after each Runner.run, we keep the `result.last_response_id`
and pass it back as `previous_response_id` on the next turn. OpenAI
manages the conversation state on their side. We store nothing but a
short string per active session.

Pods are single-replica; if a pod restarts, all session ids reset and
users start a fresh conversation, which is acceptable.
"""
import threading
import time
from collections import OrderedDict

_MAX_SESSIONS = 1000   # LRU cap (cheap — each entry is one short string)
_TTL_SECONDS = 3600    # 1 hour idle eviction


class _SessionMemory:
    def __init__(self) -> None:
        # session_key -> (last_access_monotonic, last_response_id)
        self._store: OrderedDict[str, tuple[float, str]] = OrderedDict()
        self._lock = threading.Lock()

    def _evict_stale(self) -> None:
        now = time.monotonic()
        stale = [k for k, (ts, _) in self._store.items() if now - ts > _TTL_SECONDS]
        for k in stale:
            self._store.pop(k, None)
        while len(self._store) > _MAX_SESSIONS:
            self._store.popitem(last=False)

    def get(self, session_key: str) -> str | None:
        """Return the last_response_id for this session, or None if absent/stale."""
        with self._lock:
            self._evict_stale()
            item = self._store.get(session_key)
            if item is None:
                return None
            _ts, response_id = item
            self._store[session_key] = (time.monotonic(), response_id)
            self._store.move_to_end(session_key)
            return response_id

    def put(self, session_key: str, response_id: str | None) -> None:
        """Persist the latest response_id for this session."""
        if not response_id:
            return
        with self._lock:
            self._evict_stale()
            self._store[session_key] = (time.monotonic(), response_id)
            self._store.move_to_end(session_key)

    def clear(self, session_key: str) -> None:
        with self._lock:
            self._store.pop(session_key, None)

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {"active_sessions": len(self._store)}


memory = _SessionMemory()
