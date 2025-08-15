"""Sliding-window rate limiter."""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass


@dataclass
class RateDecision:
    """Result of a rate-limit check."""

    allowed: bool
    remaining: int
    retry_after_seconds: float


class SlidingWindowLimiter:
    """Per-client sliding window rate limiter."""

    def __init__(
        self,
        requests_per_minute: int = 60,
    ) -> None:
        self._rpm = max(requests_per_minute, 1)
        self._windows: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, client_id: str) -> RateDecision:
        """Evaluate whether a request is allowed."""
        now = time.monotonic()
        window_start = now - 60.0

        with self._lock:
            if client_id not in self._windows:
                self._windows[client_id] = deque()

            window = self._windows[client_id]

            while window and window[0] < window_start:
                window.popleft()

            if len(window) >= self._rpm:
                oldest = window[0]
                retry_after = 60.0 - (now - oldest)
                return RateDecision(
                    allowed=False,
                    remaining=0,
                    retry_after_seconds=max(
                        retry_after,
                        0.0,
                    ),
                )

            window.append(now)
            remaining = self._rpm - len(window)
            return RateDecision(
                allowed=True,
                remaining=remaining,
                retry_after_seconds=0.0,
            )
