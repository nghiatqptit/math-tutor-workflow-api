from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass


class CircuitBreakerOpenError(Exception):
    pass


@dataclass
class CircuitState:
    failures: int = 0
    opened_at: float | None = None


class CircuitBreaker:
    def __init__(self, threshold: int, reset_seconds: int) -> None:
        self._threshold = threshold
        self._reset_seconds = reset_seconds
        self._state = CircuitState()
        self._lock = asyncio.Lock()

    async def before_call(self) -> None:
        async with self._lock:
            if self._state.opened_at is None:
                return
            if (time.time() - self._state.opened_at) >= self._reset_seconds:
                self._state = CircuitState()
                return
            raise CircuitBreakerOpenError("Circuit breaker is open")

    async def on_success(self) -> None:
        async with self._lock:
            self._state = CircuitState()

    async def on_failure(self) -> None:
        async with self._lock:
            self._state.failures += 1
            if self._state.failures >= self._threshold:
                self._state.opened_at = time.time()
