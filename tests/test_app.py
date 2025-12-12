import os
import sys
from pathlib import Path

os.environ.setdefault("API_KEY", "test-key")

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.main import create_app
from app.config import Settings
from app.model import model
from app.targets import GENERIC_CLASSES


def test_health_route():
    app = create_app(Settings(api_key="test"))
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_authentication_required():
    app = create_app(Settings(api_key="secret"))
    client = TestClient(app)

    response = client.post("/analyze", files={"file": ("video.mp4", b"data")})
    assert response.status_code == 401


def test_api_key_authentication():
    app = create_app(Settings(api_key="secret"))
    client = TestClient(app)

    response = client.post(
        "/analyze",
        headers={"x-api-key": "secret"},
        files={"file": ("video.mp4", b"data")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["filename"].endswith(".mp4")
    assert "labels" in payload


def test_targets_endpoint_and_model_labels():
    app = create_app(Settings(api_key="secret"))
    client = TestClient(app)

    response = client.get("/targets")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == len(GENERIC_CLASSES)
    assert payload[0]["value"] == GENERIC_CLASSES[0].value

    assert set(model.labels) == {target.label for target in GENERIC_CLASSES}
