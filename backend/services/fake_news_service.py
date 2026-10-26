"""Fake news detection service with strict trained model loader and preprocessing."""

import os
import re
from pathlib import Path
from typing import Any, Tuple
from backend.config import MODELS_DIR
from backend.schemas import FakeNewsDetectionResult
from backend.utils.logging import get_logger
from backend.validators import validate_news_input

logger = get_logger("smartshield.fake_news")

NEWS_RECOMMENDATIONS = [
    "Check if other reputable, independent news organizations are reporting the same story.",
    "Verify primary quotes, official government releases, or scientific study links cited in the text.",
    "Consult dedicated non-partisan fact-checking organizations (e.g. Snopes, PolitiFact, AP Fact Check).",
]


def preprocess_text(text: str) -> str:
    """
    Cleans and standardizes article text prior to feature extraction.
    Removes excessive whitespaces, URLs, control characters, and standardizes casing.
    """
    # Replace URLs with placeholder or remove
    cleaned = re.sub(r"https?://\S+|www\.\S+", "", text)
    # Strip HTML tags if any were pasted
    cleaned = re.sub(r"<.*?>", "", cleaned)
    # Normalize whitespaces and newlines
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.lower()


class FakeNewsService:
    """
    Handles fake news text analysis via a trained machine learning model and vectorizer.
    If no trained model artifacts are present on disk, returns an honest 'model_unavailable' status.
    """

    def __init__(self, models_dir: Path = MODELS_DIR):
        self.models_dir = Path(models_dir)
        self._model: Any = None
        self._vectorizer: Any = None
        self._load_attempted = False

    def is_model_available(self) -> bool:
        """Checks if a valid trained model and vectorizer are loaded in memory."""
        self._ensure_loaded()
        return self._model is not None and self._vectorizer is not None

    def _ensure_loaded(self) -> None:
        """Attempts to load model artifacts from disk if not previously attempted."""
        if self._load_attempted:
            return
        self._load_attempted = True

        # Check for model and vectorizer filenames
        model_paths = [
            self.models_dir / "fake_news_model.joblib",
            self.models_dir / "fake_news_model.pkl",
        ]
        vectorizer_paths = [
            self.models_dir / "fake_news_vectorizer.joblib",
            self.models_dir / "fake_news_vectorizer.pkl",
        ]

        found_model = next((p for p in model_paths if p.is_file()), None)
        found_vec = next((p for p in vectorizer_paths if p.is_file()), None)

        if not found_model or not found_vec:
            logger.info("Fake news classification model artifacts not present on disk.")
            return

        try:
            # We attempt import of joblib if available
            import joblib  # type: ignore

            self._model = joblib.load(found_model)
            self._vectorizer = joblib.load(found_vec)
            logger.info(f"Loaded fake news model from {found_model} and vectorizer from {found_vec}")
        except Exception as e:
            logger.warning(f"Failed to load fake news model artifacts: {e}")
            self._model = None
            self._vectorizer = None

    def set_model(self, model: Any, vectorizer: Any) -> None:
        """Injects model and vectorizer (primarily used for unit testing)."""
        self._model = model
        self._vectorizer = vectorizer
        self._load_attempted = True

    def analyze(self, raw_text: str) -> FakeNewsDetectionResult:
        """
        Processes news text. Returns genuine model prediction if model is loaded,
        or 'model_unavailable' status without fabricating predictions.
        """
        validated_text = validate_news_input(raw_text)
        cleaned_text = preprocess_text(validated_text)

        if not self.is_model_available():
            # Honest, transparent behavior required by specification
            return FakeNewsDetectionResult(
                success=True,
                detector="fake_news",
                status="model_unavailable",
                model_available=False,
                label=None,
                confidence=None,
                explanation=(
                    "No trained classification model is loaded right now, so we cannot produce a prediction. "
                    "We would rather show nothing than a guess. Cross-check the claim with trusted outlets "
                    "or a fact-checking organization in the meantime."
                ),
                recommendations=NEWS_RECOMMENDATIONS,
            )

        try:
            features = self._vectorizer.transform([cleaned_text])
            prediction = self._model.predict(features)[0]

            confidence = None
            if hasattr(self._model, "predict_proba"):
                probabilities = self._model.predict_proba(features)[0]
                confidence = float(max(probabilities))

            label_str = str(prediction)
            explanation = (
                f"The model classified this content as '{label_str}'. "
                "Note that machine-learning classification is statistical guidance based on linguistic patterns, "
                "not proof of factual accuracy."
            )

            return FakeNewsDetectionResult(
                success=True,
                detector="fake_news",
                status="completed",
                model_available=True,
                label=label_str,
                confidence=round(confidence, 3) if confidence is not None else None,
                explanation=explanation,
                recommendations=NEWS_RECOMMENDATIONS,
            )
        except Exception as err:
            logger.error(f"Inference error during fake news analysis: {err}")
            return FakeNewsDetectionResult(
                success=False,
                detector="fake_news",
                status="error",
                model_available=True,
                error="Model inference encountered an unexpected failure.",
                explanation="Failed to complete model prediction on the provided text.",
                recommendations=NEWS_RECOMMENDATIONS,
            )
