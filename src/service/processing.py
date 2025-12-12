from __future__ import annotations

import base64
import io
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageStat
from fastapi import UploadFile, status

from .errors import ProcessingError

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
SUPPORTED_CONTENT_TYPES = {"image/png", "image/jpeg"}
MAX_BYTES = 5 * 1024 * 1024  # 5MB

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    label: str
    confidence: float
    box: Tuple[int, int, int, int]

    def to_dict(self) -> Dict[str, float | str | Tuple[int, int, int, int]]:
        return {
            "label": self.label,
            "confidence": round(self.confidence, 3),
            "box": self.box,
        }


def validate_file(file: UploadFile, raw: bytes) -> None:
    logger.debug("Validating file %s", file.filename)
    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ProcessingError(
            code="unsupported_file_type",
            message=f"Only {', '.join(sorted(SUPPORTED_EXTENSIONS))} files are supported.",
            http_status=status.HTTP_400_BAD_REQUEST,
        )
    if file.content_type not in SUPPORTED_CONTENT_TYPES:
        raise ProcessingError(
            code="unsupported_media_type",
            message=f"Content type must be one of {', '.join(sorted(SUPPORTED_CONTENT_TYPES))}.",
            http_status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )
    if len(raw) > MAX_BYTES:
        raise ProcessingError(
            code="file_too_large",
            message=f"File exceeds {MAX_BYTES // (1024 * 1024)}MB limit.",
            http_status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            retry_after_seconds=10,
        )


def open_image(raw: bytes) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(raw))
    except Exception as exc:  # Pillow raises various errors
        raise ProcessingError(
            code="unreadable_image",
            message="Could not read the uploaded image.",
            http_status=status.HTTP_400_BAD_REQUEST,
        ) from exc
    return image.convert("RGB")


def classify_image(image: Image.Image) -> List[Detection]:
    stat = ImageStat.Stat(image)
    channels = stat.mean[:3]
    labels = ["red", "green", "blue"]
    dominant_index = max(range(3), key=lambda idx: channels[idx])
    label = labels[dominant_index]
    confidence = min(max(channels[dominant_index] / 255, 0.01), 0.99)
    width, height = image.size
    detection = Detection(
        label=label,
        confidence=confidence,
        box=(0, 0, width - 1, height - 1),
    )
    return [detection]


def annotate_image(image: Image.Image, detections: List[Detection]) -> str:
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    try:
        font = ImageFont.load_default()
    except Exception:  # pragma: no cover - load_default is reliable but guard just in case
        font = None
    for detection in detections:
        draw.rectangle(detection.box, outline="yellow", width=3)
        label_text = f"{detection.label} ({int(detection.confidence * 100)}%)"
        draw.text((detection.box[0] + 4, detection.box[1] + 4), label_text, fill="yellow", font=font)
    buffer = io.BytesIO()
    annotated.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def summarize_detections(detections: List[Detection]) -> Dict[str, int]:
    summary: Dict[str, int] = {}
    for detection in detections:
        summary[detection.label] = summary.get(detection.label, 0) + 1
    logger.debug("Per-class summary: %s", summary)
    return summary


def analyze_upload(file: UploadFile, raw: bytes) -> Dict[str, object]:
    validate_file(file, raw)
    image = open_image(raw)
    detections = classify_image(image)
    per_class = summarize_detections(detections)
    preview = annotate_image(image, detections)
    return {
        "detections": [d.to_dict() for d in detections],
        "per_class_counts": per_class,
        "total_count": sum(per_class.values()),
        "annotated_preview": preview,
    }
