"""LRU query result cache with thread safety."""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Any

from loguru import logger


class QueryResultCache:
    """Fixed-capacity LRU cache for query results."""

    def __init__(self, capacity: int = 256) -> None:
        self._capacity = max(capacity, 1)
        self._store: OrderedDict[str, Any] = OrderedDict()
        self._lock = threading.Lock()

    def lookup(
        self,
        key: str,
    ) -> dict[str, Any] | None:
        """Retrieve cached value, promoting to MRU."""
        with self._lock:
            if key not in self._store:
                return None
            self._store.move_to_end(key)
            logger.debug("Cache hit: {}", key[:40])
            return self._store[key]  # type: ignore[no-any-return]

    def store(
        self,
        key: str,
        value: dict[str, Any],
    ) -> None:
        """Insert value, evicting LRU if full."""
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
                self._store[key] = value
                return
            if len(self._store) >= self._capacity:
                evicted_key, _ = self._store.popitem(last=False)
                logger.debug(
                    "Cache evicted: {}",
                    evicted_key[:40],
                )
            self._store[key] = value

    def current_size(self) -> int:
        """Number of entries currently cached."""
        with self._lock:
            return len(self._store)
