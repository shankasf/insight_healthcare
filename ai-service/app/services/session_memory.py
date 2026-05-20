"""In-process conversation memory keyed by session_key.

The OpenAI Agents SDK is stateless per Runner.run call. To support
multi-turn flows ("book one of those", "yes the 2pm slot", "my name is...")
we keep the conversation in pod memory only — never persisted to Postgres
(chat content storage is forbidden by spec). Pods are single-replica; if a
pod restarts, all live sessions reset, which is acceptable.
"""
import threading
import time
from collections import OrderedDict
from typing import Any

_MAX_SESSIONS = 200          # LRU cap
_TTL_SECONDS = 3600          # 1 hour idle eviction
_MAX_ITEMS_PER_SESSION = 40  # last ~40 input-items (user/assistant/tool turns)


class _SessionMemory:
    def __init__(self) -> None:
        self._store: OrderedDict[str, tuple[float, list[Any]]] = OrderedDict()
        self._lock = threading.Lock()

    def _evict_stale(self) -> None:
        now = time.monotonic()
        stale = [k for k, (ts, _) in self._store.items() if now - ts > _TTL_SECONDS]
        for k in stale:
            self._store.pop(k, None)
        while len(self._store) > _MAX_SESSIONS:
            self._store.popitem(last=False)

    def get(self, session_key: str) -> list[Any] | None:
        with self._lock:
            self._evict_stale()
            item = self._store.get(session_key)
            if item is None:
                return None
            _ts, history = item
            self._store[session_key] = (time.monotonic(), history)
            self._store.move_to_end(session_key)
            return list(history)

    def put(self, session_key: str, input_list: list[Any]) -> None:
        with self._lock:
            self._evict_stale()
            trimmed = list(input_list)[-_MAX_ITEMS_PER_SESSION:]
            self._store[session_key] = (time.monotonic(), trimmed)
            self._store.move_to_end(session_key)

    def clear(self, session_key: str) -> None:
        with self._lock:
            self._store.pop(session_key, None)

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {"active_sessions": len(self._store)}


memory = _SessionMemory()
