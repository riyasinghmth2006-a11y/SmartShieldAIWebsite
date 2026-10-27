"""Integration tests verifying full API contract, health checks, and error responses."""

import pytest


def test_health_endpoints(client):
    """Verify both /health and /api/health endpoints return 200 with valid schema."""
    for path in ["/health", "/api/health"]:
        response = client.get(path)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "models_configured" in data
        assert "scam_heuristic" in data["models_configured"]
        assert "fake_news_model" in data["models_configured"]
        assert "deepfake_model" in data["models_configured"]


def test_scam_invalid_mode(client):
    """Verify 422 Unprocessable Entity when invalid mode is supplied."""
    payload = {"mode": "invalid_mode", "content": "Sample message text here"}
    response = client.post("/api/scam/analyze", json=payload)
    assert response.status_code == 422


def test_scam_missing_content(client):
    """Verify 422 Unprocessable Entity when content is omitted."""
    payload = {"mode": "message"}
    response = client.post("/api/scam/analyze", json=payload)
    assert response.status_code == 422


def test_scam_validation_error_short(client):
    """Verify 400 Bad Request when content is under minimum length."""
    payload = {"mode": "message", "content": "a"}
    response = client.post("/api/scam/analyze", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "Input is too short" in data["detail"]


def test_fake_news_validation_error_short(client):
    """Verify 422 Unprocessable Entity when text is under min_length (20)."""
    payload = {"text": "Short headline"}
    response = client.post("/api/fake-news/analyze", json=payload)
    assert response.status_code == 422


def test_deepfake_no_file_uploaded(client):
    """Verify 422 Unprocessable Entity when file multipart is missing."""
    response = client.post("/api/deepfake/analyze")
    assert response.status_code == 422


def test_deepfake_disguised_script_rejected(client):
    """Verify 400 Bad Request when an executable/script is uploaded as a .png."""
    fake_png = b"<?php echo 'malicious'; ?>"
    files = {"file": ("exploit.png", fake_png, "image/png")}
    response = client.post("/api/deepfake/analyze", files=files)
    assert response.status_code == 400
    data = response.json()
    assert "standard PNG format headers" in data["detail"]
