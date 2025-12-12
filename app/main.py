import asyncio
import tempfile
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from .auth import verify_request
from .config import Settings, VideoAnalysisResult, get_settings
from .model import model


def _bytes_from_mb(mb: int) -> int:
    return mb * 1024 * 1024


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, max_body_size: int):
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(self, request, call_next):
        content_length = request.headers.get("content-length")
        if content_length is not None and int(content_length) > self.max_body_size:
            return JSONResponse(
                status_code=413,
                content={"detail": f"Payload too large. Max {self.max_body_size // (1024 * 1024)} MB."},
            )
        return await call_next(request)


class StaticCacheMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, cache_seconds: int):
        super().__init__(app)
        self.cache_seconds = cache_seconds

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static"):
            response.headers["Cache-Control"] = f"public, max-age={self.cache_seconds}, immutable"
        return response


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Video Analysis API")

    if settings:
        app.dependency_overrides[get_settings] = lambda: settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"]
    )
    app.add_middleware(MaxBodySizeMiddleware, max_body_size=_bytes_from_mb(settings.upload_max_mb))
    app.add_middleware(StaticCacheMiddleware, cache_seconds=settings.static_cache_seconds)

    app.mount("/static", StaticFiles(directory="static", html=True), name="static")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/analyze", response_model=VideoAnalysisResult, dependencies=[Depends(verify_request)])
    async def analyze_video(
        file: UploadFile = File(...),
        settings: Settings = Depends(get_settings),
    ) -> VideoAnalysisResult:
        suffix = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            path = Path(tmp.name)

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(model.analyze, path),
                timeout=settings.video_process_timeout,
            )
        except asyncio.TimeoutError as exc:
            raise HTTPException(status_code=504, detail="Video processing timed out") from exc
        finally:
            if path.exists():
                path.unlink(missing_ok=True)

        return result

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        timeout_keep_alive=15,
    )
