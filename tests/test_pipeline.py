import base64
import os
import tempfile

import pytest
from PIL import Image

from app.metrics import RequestMetrics
from app.pipeline import RequestProcessor, StaticDetector, TransientError
from app.preview import Detection, PreviewGenerator
from app.validator import FileValidator


def create_image(path: str) -> None:
    image = Image.new("RGB", (100, 100), color="white")
    image.save(path)


def test_process_returns_counts_preview_and_timing():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        create_image(handle.name)
        image_path = handle.name

    detections = [
        Detection(label="cat", bbox=(10, 10, 40, 40), score=0.9),
        Detection(label="dog", bbox=(50, 50, 80, 80), score=0.8),
        Detection(label="cat", bbox=(20, 60, 40, 90), score=0.7),
    ]
    detector = StaticDetector({image_path: detections})
    processor = RequestProcessor(
        validator=FileValidator({".png"}),
        detector=detector,
        metrics=RequestMetrics(),
        preview_generator=PreviewGenerator(),
        retries=1,
    )

    payload = processor.process(image_path)

    assert payload.total == 3
    assert payload.per_class_counts == {"cat": 2, "dog": 1}
    assert payload.processing_time > 0
    assert base64.b64decode(payload.preview_base64).startswith(b"\x89PNG")

    os.remove(image_path)


def test_retry_on_transient_error():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        create_image(handle.name)
        image_path = handle.name

    class FlakyDetector:
        def __init__(self):
            self.calls = 0

        def detect(self, _):
            self.calls += 1
            if self.calls == 1:
                raise TransientError("temporary")
            return [Detection(label="cat", bbox=(0, 0, 10, 10), score=0.5)]

    detector = FlakyDetector()
    processor = RequestProcessor(
        validator=FileValidator({".png"}),
        detector=detector,
        metrics=RequestMetrics(),
        preview_generator=PreviewGenerator(),
        retries=1,
    )

    payload = processor.process(image_path)
    assert payload.total == 1
    assert detector.calls == 2

    os.remove(image_path)


def test_retry_exhaustion_raises():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        create_image(handle.name)
        image_path = handle.name

    class AlwaysFailDetector:
        def detect(self, _):
            raise TransientError("still failing")

    processor = RequestProcessor(
        validator=FileValidator({".png"}),
        detector=AlwaysFailDetector(),
        metrics=RequestMetrics(),
        preview_generator=PreviewGenerator(),
        retries=0,
    )

    with pytest.raises(TransientError):
        processor.process(image_path)

    os.remove(image_path)
