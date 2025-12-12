import mimetypes
import os
from dataclasses import dataclass
from typing import Iterable


@dataclass
class FileValidationResult:
    path: str
    size_bytes: int
    mime_type: str


class FileValidationError(ValueError):
    pass


class FileValidator:
    def __init__(self, allowed_extensions: Iterable[str], max_megabytes: float = 5.0) -> None:
        self.allowed_extensions = {ext.lower() for ext in allowed_extensions}
        self.max_bytes = max_megabytes * 1024 * 1024

    def validate(self, path: str) -> FileValidationResult:
        if not os.path.exists(path):
            raise FileValidationError(f"File not found: {path}")

        size_bytes = os.path.getsize(path)
        if size_bytes > self.max_bytes:
            raise FileValidationError(
                f"File too large: {size_bytes} bytes exceeds limit of {self.max_bytes} bytes"
            )

        _, ext = os.path.splitext(path)
        if ext.lower() not in self.allowed_extensions:
            raise FileValidationError(f"Unsupported file type: {ext}")

        mime_type, _ = mimetypes.guess_type(path)
        return FileValidationResult(path=path, size_bytes=size_bytes, mime_type=mime_type or "unknown")
