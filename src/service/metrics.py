from __future__ import annotations

import logging
import threading
import time
from collections import deque
from typing import Deque, List

logger = logging.getLogger(__name__)


class RequestMetrics:
    """Thread-safe in-memory recorder for request timings."""

    def __init__(self, max_samples: int = 500) -> None:
        self._durations: Deque[float] = deque(maxlen=max_samples)
        self._lock = threading.Lock()

    def record(self, duration_ms: float) -> None:
        with self._lock:
            self._durations.append(duration_ms)
        logger.debug("Recorded duration: %.2f ms", duration_ms)

    def percentile(self, percentile: float) -> float:
        with self._lock:
            if not self._durations:
                return 0.0
            sorted_values: List[float] = sorted(self._durations)
        k = (len(sorted_values) - 1) * percentile / 100
        f = int(k)
        c = min(f + 1, len(sorted_values) - 1)
        if f == c:
            return sorted_values[int(k)]
        d0 = sorted_values[f] * (c - k)
        d1 = sorted_values[c] * (k - f)
        return d0 + d1

    def p95(self) -> float:
        return self.percentile(95)


class TimingMiddleware:
    """ASGI middleware that records request timings."""

    def __init__(self, metrics: RequestMetrics) -> None:
        self.metrics = metrics

    async def __call__(self, request, call_next):  # type: ignore[override]
        start = time.perf_counter()
        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self.metrics.record(duration_ms)
            logger.info(
                "request_timing path=%s duration_ms=%.2f p95_ms=%.2f",
                request.url.path,
                duration_ms,
                self.metrics.p95(),
            )
