import tempfile
from collections import Counter
from pathlib import Path
from typing import Dict, List

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from ultralytics import YOLO

app = FastAPI(title="YOLO Detection Service")


class DetectionResult:
    def __init__(self, label: str, confidence: float, box: Dict[str, float]):
        self.label = label
        self.confidence = confidence
        self.box = box

    def to_dict(self) -> Dict[str, object]:
        return {
            "label": self.label,
            "confidence": self.confidence,
            "box": self.box,
        }


def load_model() -> YOLO:
    try:
        return YOLO("yolov8n.pt")
    except Exception as exc:  # pragma: no cover - defensive
        raise RuntimeError("Failed to load YOLO model") from exc


def read_image_bytes(file_bytes: bytes) -> np.ndarray:
    array = np.frombuffer(file_bytes, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Unable to decode image bytes")
    return image


def run_inference(image: np.ndarray, model: YOLO) -> List[DetectionResult]:
    outputs = model(image)[0]
    detections: List[DetectionResult] = []
    for box, cls_id, conf in zip(outputs.boxes.xyxy, outputs.boxes.cls, outputs.boxes.conf):
        x1, y1, x2, y2 = [float(v) for v in box.tolist()]
        label = outputs.names[int(cls_id)]
        detections.append(
            DetectionResult(
                label=label,
                confidence=float(conf),
                box={"x1": x1, "y1": y1, "x2": x2, "y2": y2},
            )
        )
    return detections


MODEL = load_model()


@app.post("/detect")
async def detect(file: UploadFile = File(...), sample_n: int = 5):
    if sample_n < 1:
        raise HTTPException(status_code=400, detail="sample_n must be at least 1")

    content_type = file.content_type or ""
    suffix = Path(file.filename or "").suffix.lower()
    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    is_video = content_type.startswith("video/") or suffix in {".mp4", ".avi", ".mov", ".mkv"}

    if not is_video:
        try:
            image = read_image_bytes(file_bytes)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        detections = run_inference(image, MODEL)
        counts = Counter(d.label for d in detections)

        return JSONResponse(
            {
                "source_type": "image",
                "frame_samples": [
                    {
                        "frame_index": 0,
                        "detections": [d.to_dict() for d in detections],
                        "counts": counts,
                    }
                ],
                "aggregate_counts": counts,
            }
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix or ".mp4") as temp_video:
        temp_video.write(file_bytes)
        video_path = temp_video.name

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise HTTPException(status_code=400, detail="Unable to read uploaded video")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    interval = max(total_frames // sample_n, 1) if total_frames > 0 else 1

    frame_results = []
    aggregate_counts: Counter[str] = Counter()
    frame_idx = 0
    samples_taken = 0

    while cap.isOpened() and samples_taken < sample_n:
        success, frame = cap.read()
        if not success:
            break

        if total_frames == 0 or frame_idx % interval == 0:
            detections = run_inference(frame, MODEL)
            counts = Counter(d.label for d in detections)
            aggregate_counts.update(counts)
            frame_results.append(
                {
                    "frame_index": frame_idx,
                    "detections": [d.to_dict() for d in detections],
                    "counts": counts,
                }
            )
            samples_taken += 1

        frame_idx += 1

    cap.release()
    Path(video_path).unlink(missing_ok=True)

    if not frame_results:
        raise HTTPException(status_code=400, detail="No frames processed from video")

    return JSONResponse(
        {
            "source_type": "video",
            "sampled_frames": len(frame_results),
            "frame_samples": frame_results,
            "aggregate_counts": aggregate_counts,
            "frame_stride": interval,
        }
    )


@app.get("/")
async def root():
    return {"message": "YOLO detection service is running", "detect_endpoint": "/detect"}
