import logging
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List

from .metrics import RequestMetrics
from .preview import Detection, PreviewGenerator
from .validator import FileValidationError, FileValidator


class TransientError(RuntimeError):
    pass


@dataclass
class ResponsePayload:
    per_class_counts: Dict[str, int]
    total: int
    preview_base64: bytes
    processing_time: float


class RequestProcessor:
    def __init__(
        self,
        validator: FileValidator,
        detector,
        metrics: RequestMetrics,
        preview_generator: PreviewGenerator,
        retries: int = 1,
    ) -> None:
        self.validator = validator
        self.detector = detector
        self.metrics = metrics
        self.preview_generator = preview_generator
        self.retries = retries

    def _aggregate_counts(self, detections: Iterable[Detection]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for det in detections:
            counts[det.label] = counts.get(det.label, 0) + 1
        return counts

    def _detect_with_retry(self, image_path: str) -> List[Detection]:
        attempts = 0
        last_error: Exception | None = None
        while attempts <= self.retries:
            try:
                return list(self.detector.detect(image_path))
            except TransientError as exc:  # type: ignore[unreachable]
                attempts += 1
                last_error = exc
                logging.warning("Transient detection error (attempt %s/%s): %s", attempts, self.retries + 1, exc)
                time.sleep(0.01)
        assert last_error is not None
        raise last_error

    def process(self, image_path: str) -> ResponsePayload:
        validation = self.validator.validate(image_path)
        logging.info("Validated %s (size=%sb, mime=%s)", validation.path, validation.size_bytes, validation.mime_type)

        with self.metrics.time_request():
            detections = self._detect_with_retry(image_path)

        counts = self._aggregate_counts(detections)
        total = sum(counts.values())
        _, encoded_preview = self.preview_generator.annotate(image_path, detections)

        self.metrics.log_percentiles()

        return ResponsePayload(
            per_class_counts=counts,
            total=total,
            preview_base64=encoded_preview,
            processing_time=self.metrics.durations[-1] if self.metrics.durations else 0.0,
        )


class StaticDetector:
    """Deterministic detector used for tests and offline validation."""

    def __init__(self, mapping: Dict[str, List[Detection]]) -> None:
        self.mapping = mapping

    def detect(self, image_path: str) -> Iterable[Detection]:
        if image_path not in self.mapping:
            raise TransientError(f"No detection mapping found for {image_path}")
        return self.mapping[image_path]
