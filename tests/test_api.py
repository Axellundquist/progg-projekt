import base64
import io

from fastapi.testclient import TestClient
from PIL import Image

from service.app import app
from service.processing import MAX_BYTES

client = TestClient(app)


def _make_image(color):
    img = Image.new("RGB", (64, 64), color=color)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def test_analyze_returns_counts_and_preview():
    response = client.post(
        "/analyze",
        files={"file": ("red.png", _make_image((255, 20, 20)), "image/png")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["per_class_counts"] == {"red": 1}
    assert payload["total_count"] == 1
    assert payload["detections"][0]["label"] == "red"
    preview = payload["annotated_preview"]
    assert preview.startswith("data:image/png;base64,")
    base64.b64decode(preview.split(",", 1)[1])  # ensure valid


def test_validation_blocks_invalid_type():
    response = client.post(
        "/analyze",
        files={"file": ("note.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error"] == "unsupported_file_type"


def test_validation_blocks_large_payload():
    oversized = io.BytesIO(b"0" * (MAX_BYTES + 1))
    response = client.post(
        "/analyze",
        files={"file": ("big.png", oversized, "image/png")},
    )
    assert response.status_code == 413
    detail = response.json()["detail"]
    assert detail["retry_after_seconds"] == 10
