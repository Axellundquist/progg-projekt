import logging
import statistics
import time
from contextlib import contextmanager
from typing import List


class RequestMetrics:
    """Collects request durations and logs percentile latency."""

    def __init__(self) -> None:
        self.durations: List[float] = []

    @contextmanager
    def time_request(self):
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self.record(elapsed)

    def record(self, duration: float) -> None:
        self.durations.append(duration)
        logging.debug("Recorded request duration %.4f seconds", duration)

    def p95(self) -> float:
        if not self.durations:
            return 0.0
        if len(self.durations) < 2:
            return self.durations[0]

        # statistics.quantiles returns exclusive quantiles with method='exclusive' default.
        # Using n=20 yields the 95th percentile.
        quantiles = statistics.quantiles(self.durations, n=20)
        return quantiles[18]

    def log_percentiles(self) -> None:
        p95 = self.p95()
        logging.info("Request latency P95: %.3fms", p95 * 1000)


# Configure a default logger for local runs/tests.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
