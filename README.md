# Image Analysis Service

Simple FastAPI service that validates uploads, annotates previews with detected labels, and surfaces timing metrics.

## Running

```bash
pip install -r requirements.txt
uvicorn service.app:app --reload
```

## Features
- Request timing middleware logs per-request latency and current P95.
- Upload validation for image type and 5MB size cap with structured retry hints.
- Annotated preview with labels alongside per-class and total counts in the response.
- Evaluation helpers plus a tiny test set to validate precision/recall and counting error.

## Tests

```bash
pytest
```
