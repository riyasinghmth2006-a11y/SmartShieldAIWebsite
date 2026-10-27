"""Tests for the new detect endpoints: spam, fakenews, and deepfake."""

import io
from PIL import Image
import pytest


def test_spam_detect_spam_message(client):
    payload = {"text": "URGENT: Your account will be suspended within 24 hours. Verify credentials at http://bank-update.xyz or pay fee in gift cards."}
    response = client.post("/api/spam/detect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["label"] == "spam"
    assert data["confidence"] >= 0.5
    assert len(data["reasons"]) > 0
    assert "model" in data


def test_spam_detect_ham_message(client):
    payload = {"text": "Hey, can we schedule our meeting for tomorrow at 2 PM in conference room B?"}
    response = client.post("/api/spam/detect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["label"] == "ham"
    assert "model" in data


def test_spam_detect_empty_validation(client):
    response = client.post("/api/spam/detect", json={"text": "   "})
    assert response.status_code == 400


def test_fakenews_detect_endpoint(client):
    payload = {"text": "Scientists announce miracle fruit that cures all cancer overnight without side effects."}
    response = client.post("/api/fakenews/detect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["label"] in ["potentially_false", "potentially_authentic"]
    assert "confidence" in data
    assert data["verification_status"] == "unverified"
    assert "explanation" in data


def test_fakenews_detect_hindi_limitation(client):
    payload = {"text": "यह एक हिंदी समाचार लेख है जो एक आश्चर्यजनक खोज का दावा करता है।"}
    response = client.post("/api/fakenews/detect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["limitations"]) > 0
    assert any("English" in lim or "Hindi" in lim for lim in data["limitations"])


def test_deepfake_detect_endpoint(client):
    img = Image.new("RGB", (224, 224), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    files = {"file": ("test_photo.png", buf.getvalue(), "image/png")}
    response = client.post("/api/deepfake/detect", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["label"] in [
        "Potentially AI-Generated",
        "Potentially Manipulated",
        "No Strong Manipulation Signals Detected",
    ]
    assert "confidence" in data
    assert data["verification_status"] == "unverified"
    assert "media_summary" in data
    assert data["media_summary"]["extension"] == "PNG"
