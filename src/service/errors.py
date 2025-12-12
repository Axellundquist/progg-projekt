from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from fastapi import HTTPException, status


@dataclass
class ProcessingError(Exception):
    """Structured error that carries metadata for the client."""

    code: str
    message: str
    http_status: int = status.HTTP_400_BAD_REQUEST
    retry_after_seconds: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "error": self.code,
            "message": self.message,
        }
        if self.retry_after_seconds is not None:
            payload["retry_after_seconds"] = self.retry_after_seconds
        return payload


def as_http_exception(error: ProcessingError) -> HTTPException:
    return HTTPException(status_code=error.http_status, detail=error.to_dict())
