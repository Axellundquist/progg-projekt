# Video Analysis API

A small FastAPI service that simulates video analysis behind simple authentication. It enforces upload size limits, caches static assets, and includes containerization for local or GPU-enabled deployments.

## Features
- API key or HTTP basic authentication on the `/analyze` endpoint.
- Upload size limit configurable via `UPLOAD_MAX_MB`; returns `413` when exceeded.
- Static assets served from `/static` with long-lived cache headers (CDN-friendly).
- Video processing wrapped in a timeout (`VIDEO_PROCESS_TIMEOUT`) to prevent runaway jobs.
- Dockerfile and `docker-compose.yml` for CPU or GPU-backed instances.

## Quickstart (local)
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```
2. Set minimal environment (at least `API_KEY`):
   ```bash
   export API_KEY=dev-key
   export BASIC_AUTH_USER=dev
   export BASIC_AUTH_PASSWORD=devpass
   ```
3. Run the API:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --timeout-keep-alive 15
   ```
4. Test authentication and upload limit:
   ```bash
   curl -H "x-api-key: $API_KEY" -F "file=@/path/to/video.mp4" http://localhost:8000/analyze
   ```

## Docker
Build and run the containerized API:
```bash
API_KEY=dev-key \
BASIC_AUTH_USER=dev \ 
BASIC_AUTH_PASSWORD=devpass \ 
UPLOAD_MAX_MB=100 \ 
VIDEO_PROCESS_TIMEOUT=180 \ 
docker build -t video-analysis-api .
docker run -p 8000:8000 --env API_KEY --env BASIC_AUTH_USER --env BASIC_AUTH_PASSWORD \
  --env UPLOAD_MAX_MB --env VIDEO_PROCESS_TIMEOUT video-analysis-api
```

## Docker Compose
Use compose for easy overrides and static volume mounting:
```bash
docker compose up --build
```
Environment variables can be provided in a `.env` file or via the shell. To run with GPU support on a compatible host, add `--gpus all`:
```bash
docker compose run --gpus all api
```
The compose file includes a `deploy.resources` GPU reservation for schedulers that honor it.

## Running on a small GPU VM
1. Provision a VM with the NVIDIA container runtime (e.g., `nvidia-container-toolkit` installed) and Docker/Compose.
2. Clone the repo and export environment variables (API key/auth secrets, timeouts, limits).
3. Build and start with Compose, enabling GPUs: `docker compose up --build --gpus all`.
4. Front a CDN or reverse proxy (e.g., Cloudflare, Nginx) for static caching; `/static` responses include `Cache-Control: public, max-age=<STATIC_CACHE_SECONDS>, immutable`.

## Configuration
| Variable | Default | Description |
| --- | --- | --- |
| `API_KEY` | _required_ | API key checked on `x-api-key` header. |
| `BASIC_AUTH_USER` | `null` | Optional basic auth username (pair with `BASIC_AUTH_PASSWORD`). |
| `BASIC_AUTH_PASSWORD` | `null` | Optional basic auth password. |
| `UPLOAD_MAX_MB` | `50` | Maximum allowed request size in megabytes. |
| `VIDEO_PROCESS_TIMEOUT` | `120` | Timeout (seconds) for video analysis. |
| `STATIC_CACHE_SECONDS` | `31536000` | Cache lifetime for static assets. |

## Static assets and CDN
Static files are mounted at `/static`. Cache headers allow edge/CDN caching; the mounted directory is read-only in Compose to keep deployments reproducible.

## Testing
Run the lightweight test suite:
```bash
pytest
```
