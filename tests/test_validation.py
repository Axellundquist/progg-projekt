import os
import tempfile

import pytest

from app.validator import FileValidationError, FileValidator


def test_validate_allows_configured_type_and_size():
    validator = FileValidator(allowed_extensions={".png"}, max_megabytes=0.1)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        handle.write(b"0" * 1024)
        path = handle.name

    result = validator.validate(path)
    assert result.path == path
    assert result.size_bytes == 1024
    assert result.mime_type == "image/png"
    os.remove(path)


def test_validate_rejects_unsupported_type():
    validator = FileValidator(allowed_extensions={".png"})
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as handle:
        path = handle.name

    with pytest.raises(FileValidationError):
        validator.validate(path)
    os.remove(path)


def test_validate_rejects_large_files():
    validator = FileValidator(allowed_extensions={".png"}, max_megabytes=0.0001)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        handle.write(b"0" * 1024)
        path = handle.name

    with pytest.raises(FileValidationError):
        validator.validate(path)
    os.remove(path)
