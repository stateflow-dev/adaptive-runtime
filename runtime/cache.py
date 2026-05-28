"""
Lightweight TTL-based in-memory cache for the runtime.
"""

import time
from threading import Lock


class TTLCache:
    """
    Simple thread-safe in-memory cache with per-entry TTL.
    Suitable for deduplicating events, caching context results, etc.
    """

    def __init__(self, default_ttl: float = 60.0):
        self._store: dict[str, tuple[any, float]] = {}  # key → (value, expires_at)
        self._default_ttl = default_ttl
        self._lock = Lock()

    def set(self, key: str, value, ttl: float | None = None) -> None:
        expires = time.monotonic() + (ttl if ttl is not None else self._default_ttl)
        with self._lock:
            self._store[key] = (value, expires)

    def get(self, key: str):
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires = entry
            if time.monotonic() > expires:
                del self._store[key]
                return None
            return value

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def purge_expired(self) -> int:
        now = time.monotonic()
        with self._lock:
            expired = [k for k, (_, exp) in self._store.items() if now > exp]
            for k in expired:
                del self._store[k]
        return len(expired)

    def __len__(self) -> int:
        self.purge_expired()
        return len(self._store)
