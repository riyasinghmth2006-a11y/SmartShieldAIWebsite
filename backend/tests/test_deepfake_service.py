"""Automated unit and integration tests for DeepfakeService."""

import pytest
from backend.services.deepfake_service import DeepfakeService
from backend.validators import ValidationError


@pytest.fixture
def deepfake_service(tmp_path):
    return DeepfakeService(models_dir=tmp_path)


# Valid headers for testing
PNG_HEADER = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPEG_HEADER = b"\xff\xd8\xff\xe0" + b"\x00" * 32
CORRUPT_BYTES = b"NOT_AN_IMAGE_FILE_DATA_HERE"


def test_valid_png_acceptance(deepfake_service):
    res = deepfake_service.analyze_image("sample_screenshot.png", PNG_HEADER)
    assert res.success is True
    assert res.status == "model_unavailable"
    assert res.media_summary["kind"] == "image"
    assert res.media_summary["extension"] == "PNG"


def test_valid_jpeg_acceptance(deepfake_service):
    res = deepfake_service.analyze_image("portrait.jpg", JPEG_HEADER)
    assert res.success is True
    assert res.media_summary["extension"] == "JPG"


def test_corrupt_magic_bytes_rejected(deepfake_service):
    with pytest.raises(ValidationError) as exc_info:
        deepfake_service.analyze_image("fake_image.png", CORRUPT_BYTES)
    assert "standard PNG format headers" in str(exc_info.value)


def test_unsupported_file_extension(deepfake_service):
    with pytest.raises(ValidationError) as exc_info:
        deepfake_service.analyze_image("script.exe", b"MZ" + b"\x00" * 10)
    assert "Invalid file type" in str(exc_info.value)


def test_empty_file_rejected(deepfake_service):
    with pytest.raises(ValidationError):
        deepfake_service.analyze_image("empty.png", b"")


def test_oversized_file_rejected(deepfake_service):
    huge_payload = b"\x89PNG\r\n\x1a\n" + (b"\x00" * (11 * 1024 * 1024))
    with pytest.raises(ValidationError) as exc_info:
        deepfake_service.analyze_image("huge.png", huge_payload)
    assert "exceeds maximum allowed limit" in str(exc_info.value)


def test_path_traversal_sanitized(deepfake_service):
    res = deepfake_service.analyze_image("../../../etc/passwd.png", PNG_HEADER)
    assert res.media_summary["name"] == "passwd.png"


# Valid minimal 1x1 PNG image
VALID_PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)


def test_api_deepfake_endpoint(client):
    files = {"file": ("test.png", VALID_PNG_BYTES, "image/png")}
    response = client.post("/api/deepfake/analyze", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["detector"] == "deepfake"
    assert data["status"] in ["model_unavailable", "completed"]
    assert "media_summary" in data
    if data["status"] == "completed":
        assert data["label"] is not None
        assert data["confidence"] is not None


def test_api_deepfake_corrupt_stream_returns_400(client):
    files = {"file": ("corrupt.png", PNG_HEADER, "image/png")}
    response = client.post("/api/deepfake/analyze", files=files)
    # Truncated 40-byte PNG header fails full image decoding
    assert response.status_code == 400

