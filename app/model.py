import random
import time
from pathlib import Path

from .config import VideoAnalysisResult
from .targets import GENERIC_CLASSES


class SimpleVideoModel:
    """A placeholder video model that simulates inference work."""

    def __init__(self, labels: list[str] | None = None):
        self.labels = labels or [target.label for target in GENERIC_CLASSES]

    def analyze(self, path: Path) -> VideoAnalysisResult:
        # Pretend to "load" and process a video file; keep it fast for local testing.
        fake_duration = round(random.uniform(0.5, 5.0), 2)
        time.sleep(0.2)
        detected = random.sample(self.labels, k=min(2, len(self.labels)))
        return VideoAnalysisResult(
            filename=path.name,
            duration_seconds=fake_duration,
            labels=detected,
        )


model = SimpleVideoModel()
