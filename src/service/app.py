from __future__ import annotations

import logging
import time
from typing import Dict

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

from .errors import ProcessingError, as_http_exception
from .metrics import RequestMetrics, TimingMiddleware
from .processing import analyze_upload

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Image Analysis Service", version="1.0.0")
metrics = RequestMetrics()
app.middleware("http")(TimingMiddleware(metrics))


@app.exception_handler(ProcessingError)
async def processing_error_handler(_, exc: ProcessingError):
    return JSONResponse(status_code=exc.http_status, content={'detail': exc.to_dict()})


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)) -> Dict[str, object]:
    start = time.perf_counter()
    raw = await file.read()
    try:
        payload = analyze_upload(file, raw)
    except ProcessingError:
        raise
    except Exception as exc:  # pragma: no cover - guardrail for unexpected errors
        logger.exception("Unexpected error while analyzing file")
        raise as_http_exception(
            ProcessingError(
                code="internal_error",
                message="Temporary processing issue. Please retry.",
                retry_after_seconds=5,
            )
        ) from exc
    payload["processing_time_ms"] = round((time.perf_counter() - start) * 1000, 2)
    return payload


@app.get("/metrics")
async def metrics_endpoint() -> Dict[str, float]:
    return {"p95_ms": metrics.p95()}


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}
