"""Automated unit and integration tests for FakeNewsService."""

import pytest
from backend.services.fake_news_service import FakeNewsService, preprocess_text
from backend.validators import ValidationError


@pytest.fixture
def fake_news_service(tmp_path):
    # Pass an empty temporary directory so no model is found
    return FakeNewsService(models_dir=tmp_path)


def test_preprocessing():
    raw = "BREAKING NEWS: <b>Miracle cure</b> found at https://example.com/cure  !! "
    processed = preprocess_text(raw)
    assert "<b>" not in processed
    assert "https://" not in processed
    assert "breaking news: miracle cure found at !!" == processed


def test_missing_model_returns_model_unavailable(fake_news_service):
    text = "Scientists announce miracle fruit that cures every disease overnight, doctors stunned."
    res = fake_news_service.analyze(text)
    assert res.success is True
    assert res.status == "model_unavailable"
    assert res.model_available is False
    assert res.label is None
    assert "No trained classification model is loaded" in res.explanation


def test_mock_model_inference_when_loaded(fake_news_service):
    class MockVectorizer:
        def transform(self, texts):
            return texts

    class MockClassifier:
        def predict(self, features):
            return ["Unverified / Questionable"]

        def predict_proba(self, features):
            return [[0.15, 0.85]]

    fake_news_service.set_model(MockClassifier(), MockVectorizer())
    text = "Scientists announce miracle fruit that cures every disease overnight, doctors stunned."
    res = fake_news_service.analyze(text)
    assert res.success is True
    assert res.status == "completed"
    assert res.model_available is True
    assert res.label == "Unverified / Questionable"
    assert res.confidence == 0.85


def test_short_news_text_rejected(fake_news_service):
    with pytest.raises(ValidationError):
        fake_news_service.analyze("Too short headline")


def test_api_fake_news_endpoint(client):
    payload = {
        "text": "Scientists announce miracle fruit that cures every disease overnight, doctors stunned."
    }
    response = client.post("/api/fake-news/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["detector"] == "fake_news"
    assert data["status"] in ["model_unavailable", "completed"]
    assert "recommendations" in data
