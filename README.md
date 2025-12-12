# progg-projekt

This repository contains a small, testable reference pipeline for validating image uploads, capturing request timing, generating annotated previews, and evaluating detection quality.

## Key components
- **Request timing and logging** via `RequestMetrics` with P95 logging after each request.
- **File validation** (`FileValidator`) that enforces allowed extensions and size limits.
- **Per-class and total counting** returned by `RequestProcessor.process`, including base64-encoded annotated previews from `PreviewGenerator`.
- **Error/retry flow** for transient detector failures, with warnings on retry.
- **Evaluation helpers** (`evaluate_dataset`) and a small JSON test set for verifying precision/recall and counting error targets.

## Running tests
Install dependencies and execute the test suite:

```bash
pip install -r requirements.txt
pytest
```
