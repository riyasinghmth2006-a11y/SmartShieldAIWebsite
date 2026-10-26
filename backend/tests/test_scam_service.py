"""Automated unit and integration tests for ScamService."""

import pytest
from backend.services.scam_service import ScamService
from backend.validators import ValidationError


@pytest.fixture
def scam_service():
    return ScamService()


def test_detect_urgency_signal(scam_service):
    text = "URGENT: Act now within 24 hours or your account will be suspended immediately."
    res = scam_service.analyze(text, mode="message")
    assert res.success is True
    assert any(h.id == "urgency" for h in res.hits)
    assert res.level in ["Some signals", "Multiple signals"]
    assert res.risk_score > 0.0


def test_detect_sensitive_credential_request(scam_service):
    text = "Please verify your account by providing your password and social security number."
    res = scam_service.analyze(text, mode="message")
    assert any(h.id == "sensitive" for h in res.hits)


def test_detect_unusual_payment(scam_service):
    text = "To release your package, pay a processing fee in bitcoin or gift cards."
    res = scam_service.analyze(text, mode="message")
    assert any(h.id == "payment" for h in res.hits)


def test_detect_suspicious_url_characteristics(scam_service):
    url = "http://192.168.1.1/login-update-account.xyz"
    res = scam_service.analyze(url, mode="url")
    assert any(h.id == "url" for h in res.hits)
    assert res.level in ["Some signals", "Multiple signals"]


def test_benign_message_no_signals(scam_service):
    text = "Hey, are we still meeting for lunch at 1pm tomorrow near the library?"
    res = scam_service.analyze(text, mode="message")
    assert res.level == "None found"
    assert len(res.hits) == 0
    assert res.risk_score == 0.0


def test_validation_rejects_empty_and_short(scam_service):
    with pytest.raises(ValidationError):
        scam_service.analyze("  ", mode="message")

    with pytest.raises(ValidationError):
        scam_service.analyze("hi", mode="message")


def test_api_scam_endpoint(client):
    payload = {
        "mode": "message",
        "content": "URGENT notice: verify your password at http://secure-login.xyz to avoid suspension.",
    }
    response = client.post("/api/scam/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["detector"] == "scam"
    assert data["level"] == "Multiple signals"
    assert len(data["hits"]) >= 2
    assert "recommendations" in data
