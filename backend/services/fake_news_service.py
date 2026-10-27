
"""Fake news detection service with pretrained DistilBERT model loader and inference."""

import re
from pathlib import Path
from typing import Any, Tuple

from backend.config import MODELS_DIR
from backend.schemas import FakeNewsDetectResponse, FakeNewsDetectionResult
from backend.utils.logging import get_logger
from backend.validators import ValidationError, validate_news_input

logger = get_logger("smartshield.fake_news")

NEWS_RECOMMENDATIONS = [
    "Check if other reputable, independent news organizations are reporting the same story.",
    "Verify primary quotes, official government releases, or scientific study links cited in the text.",
    "Consult dedicated non-partisan fact-checking organizations (e.g. Snopes, PolitiFact, AP Fact Check).",
]

HF_MODEL_ID = "Lennywinks/fake-news-detector-english"


def preprocess_text(text: str) -> str:
    """Clean and standardize article text."""
    cleaned = re.sub(r"https?://\S+|www\.\S+", "", text)
    cleaned = re.sub(r"<.*?>", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.lower()


class FakeNewsService:
    """Loads a Hugging Face model, with an optional legacy joblib fallback."""

    def __init__(self, models_dir: Path = MODELS_DIR):
        self.models_dir = Path(models_dir)
        self._hf_model: Any = None
        self._tokenizer: Any = None
        self._legacy_model: Any = None
        self._legacy_vectorizer: Any = None
        self._load_attempted = False

    def is_model_available(self) -> bool:
        self._ensure_loaded()
        return (
            self._hf_model is not None and self._tokenizer is not None
        ) or (
            self._legacy_model is not None
            and self._legacy_vectorizer is not None
        )

    def _ensure_loaded(self) -> None:
        """Load from Hugging Face first, then try local legacy artifacts."""
        if self._load_attempted:
            return

        self._load_attempted = True

        try:
            from transformers import (
                AutoModelForSequenceClassification,
                AutoTokenizer,
            )

            logger.info("Loading fake-news model from Hugging Face: %s", HF_MODEL_ID)

            self._tokenizer = AutoTokenizer.from_pretrained(HF_MODEL_ID)
            self._hf_model = AutoModelForSequenceClassification.from_pretrained(
                HF_MODEL_ID
            )
            self._hf_model.eval()

            logger.info(
                "Fake-news model loaded successfully. Labels: %s",
                self._hf_model.config.id2label,
            )
            return

        except Exception as e:
            logger.warning("Could not load Hugging Face model: %s", e)
            self._hf_model = None
            self._tokenizer = None

        # Fallback to existing local joblib artifacts, if available.
        model_path = self.models_dir / "fake_news_model.joblib"
        vectorizer_path = self.models_dir / "fake_news_vectorizer.joblib"

        if model_path.is_file() and vectorizer_path.is_file():
            try:
                import joblib

                self._legacy_model = joblib.load(model_path)
                self._legacy_vectorizer = joblib.load(vectorizer_path)

                logger.info("Loaded legacy fake-news model from %s", model_path)
                return

            except Exception as e:
                logger.warning("Could not load legacy model: %s", e)
                self._legacy_model = None
                self._legacy_vectorizer = None

        logger.error("No usable fake-news model is available.")

    def set_model(self, model: Any, vectorizer: Any = None) -> None:
        """Inject a model for testing."""
        if vectorizer is not None:
            self._legacy_model = model
            self._legacy_vectorizer = vectorizer
        else:
            self._hf_model = model

        self._load_attempted = True

    def _get_label_mapping(self) -> Tuple[int, int]:
        """Return real-class and fake-class indices from the model config."""
        raw_mapping = getattr(
            self._hf_model.config,
            "id2label",
            {0: "fake", 1: "real"},
        )

        mapping = {}
        for key, value in raw_mapping.items():
            index = int(key) if str(key).isdigit() else key
            mapping[index] = str(value).lower()

        real_idx = next(
            (
                key for key, value in mapping.items()
                if any(label in value for label in ("real", "true", "authentic"))
            ),
            None,
        )
        fake_idx = next(
            (
                key for key, value in mapping.items()
                if any(label in value for label in ("fake", "false", "misleading"))
            ),
            None,
        )

        if real_idx is None or fake_idx is None:
            raise ValueError(
                f"Could not identify real/fake labels in model config: {mapping}"
            )

        return real_idx, fake_idx

    def _predict(self, text: str) -> tuple[str, float]:
        """Run inference and return the label and confidence."""
        import torch

        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )

        with torch.no_grad():
            logits = self._hf_model(**inputs).logits[0]
            probabilities = torch.softmax(logits, dim=-1)

        real_idx, fake_idx = self._get_label_mapping()
        prob_real = float(probabilities[real_idx].item())
        prob_fake = float(probabilities[fake_idx].item())

        if prob_fake > prob_real:
            return "potentially_false", prob_fake

        return "potentially_authentic", prob_real

    def detect_fakenews(self, raw_text: str) -> FakeNewsDetectResponse:
        """Handle POST /api/fakenews/detect."""
        if not isinstance(raw_text, str):
            raise ValidationError("News text must be a string.")

        cleaned = raw_text.strip()

        if not cleaned:
            raise ValidationError("Please provide a news article or claim to analyze.")
        if len(cleaned) < 10:
            raise ValidationError("Please enter at least 10 characters to analyze.")
        if len(cleaned) > 20000:
            raise ValidationError("Text exceeds maximum allowed length of 20,000 characters.")

        if not self.is_model_available():
            raise ValidationError(
                "Fake news detection model is currently unavailable on the server."
            )

        limitations = []
        has_hindi = bool(re.search(r"[\u0900-\u097F]", cleaned))

        if has_hindi:
            limitations.append(
                "This model is specialized for English. Hindi predictions may be unreliable."
            )

        if self._hf_model is not None and self._tokenizer is not None:
            try:
                label, confidence = self._predict(cleaned)

                if label == "potentially_false":
                    explanation = (
                        "The model detected linguistic patterns associated with "
                        "misinformation datasets. This is not proof that the claim "
                        "is false; verify it with independent, reliable sources."
                    )
                else:
                    explanation = (
                        "The model detected patterns consistent with authentic "
                        "reporting. This is not proof that the claim is true; "
                        "verify it with independent, reliable sources."
                    )

                if has_hindi:
                    explanation += (
                        " The input contains Hindi text, which this English-focused "
                        "model may not classify reliably."
                    )

                return FakeNewsDetectResponse(
                    success=True,
                    label=label,
                    confidence=round(confidence, 2),
                    model="distilbert-fake-news-detector-english",
                    explanation=explanation,
                    verification_status="unverified",
                    limitations=limitations,
                )

            except Exception as err:
                logger.exception("Fake-news inference failed: %s", err)
                raise ValidationError(
                    "Fake-news analysis failed. Please try again later."
                )

        cleaned_text = preprocess_text(cleaned)
        features = self._legacy_vectorizer.transform([cleaned_text])
        prediction = self._legacy_model.predict(features)[0]

        confidence = 0.85
        if hasattr(self._legacy_model, "predict_proba"):
            confidence = float(max(self._legacy_model.predict_proba(features)[0]))

        label = (
            "potentially_false"
            if "fake" in str(prediction).lower()
            else "potentially_authentic"
        )

        return FakeNewsDetectResponse(
            success=True,
            label=label,
            confidence=round(confidence, 2),
            model="legacy-fake-news-classifier",
            explanation=(
                "This is a model-based classification, not proof of factual accuracy. "
                "Verify important claims independently."
            ),
            verification_status="unverified",
            limitations=limitations,
        )

    def analyze(self, raw_text: str) -> FakeNewsDetectionResult:
        """Handle the legacy /api/fake-news/analyze route."""
        validated_text = validate_news_input(raw_text)

        if not self.is_model_available():
            return FakeNewsDetectionResult(
                success=True,
                detector="fake_news",
                status="model_unavailable",
                model_available=False,
                label=None,
                confidence=None,
                explanation=(
                    "No trained classification model is available right now. "
                    "We will not guess. Cross-check this claim with trusted news "
                    "organizations and independent fact-checkers."
                ),
                recommendations=NEWS_RECOMMENDATIONS,
            )

        try:
            if self._hf_model is not None and self._tokenizer is not None:
                label, confidence = self._predict(validated_text)

                if label == "potentially_false":
                    display_label = "Potentially Fake / Misleading"
                    explanation = (
                        "The model detected patterns associated with misinformation "
                        "datasets. This is statistical guidance, not proof of a claim's "
                        "accuracy."
                    )
                else:
                    display_label = "Consistent with Authentic News"
                    explanation = (
                        "The model detected patterns consistent with factual reporting. "
                        "This is not proof that the claim is true; check primary sources."
                    )

                return FakeNewsDetectionResult(
                    success=True,
                    detector="fake_news",
                    status="completed",
                    model_available=True,
                    label=display_label,
                    confidence=round(confidence, 3),
                    model="distilbert-fake-news-detector-english",
                    explanation=explanation,
                    recommendations=NEWS_RECOMMENDATIONS,
                )

            cleaned_text = preprocess_text(validated_text)
            features = self._legacy_vectorizer.transform([cleaned_text])
            prediction = self._legacy_model.predict(features)[0]

            confidence = None
            if hasattr(self._legacy_model, "predict_proba"):
                confidence = float(
                    max(self._legacy_model.predict_proba(features)[0])
                )

            return FakeNewsDetectionResult(
                success=True,
                detector="fake_news",
                status="completed",
                model_available=True,
                label=str(prediction),
                confidence=round(confidence, 3) if confidence is not None else None,
                explanation=(
                    "This is a model-based classification, not proof of factual "
                    "accuracy. Verify important claims independently."
                ),
                recommendations=NEWS_RECOMMENDATIONS,
            )

        except Exception as err:
            logger.exception("Fake-news analysis failed: %s", err)
            return FakeNewsDetectionResult(
                success=False,
                detector="fake_news",
                status="error",
                model_available=True,
                error="Model inference encountered an unexpected failure.",
                explanation="The model could not complete the prediction.",
                recommendations=NEWS_RECOMMENDATIONS,
            )
