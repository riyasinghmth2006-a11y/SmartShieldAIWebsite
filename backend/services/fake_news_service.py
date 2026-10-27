"""Fake news detection service with pretrained DistilBERT model loader and inference."""

import os
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

# Supported model identifier
HF_MODEL_ID = "Lennywinks/fake-news-detector-english"


def preprocess_text(text: str) -> str:
    """
    Cleans and standardizes article text prior to feature extraction.
    Removes excessive whitespaces, URLs, control characters, and standardizes casing.
    """
    cleaned = re.sub(r"https?://\S+|www\.\S+", "", text)
    cleaned = re.sub(r"<.*?>", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.lower()


class FakeNewsService:
    """
    Handles fake news text analysis via the fine-tuned DistilBERT model:
    Lennywinks/fake-news-detector-english (or legacy fallback vectorizer).
    If no trained model artifacts are present on disk, returns an honest model_unavailable status.
    """

    def __init__(self, models_dir: Path = MODELS_DIR):
        self.models_dir = Path(models_dir)
        self._hf_model: Any = None
        self._tokenizer: Any = None
        self._legacy_model: Any = None
        self._legacy_vectorizer: Any = None
        self._load_attempted = False

    def is_model_available(self) -> bool:
        """Checks if a valid trained model and tokenizer/vectorizer are loaded in memory."""
        self._ensure_loaded()
        return (self._hf_model is not None and self._tokenizer is not None) or (
            self._legacy_model is not None and self._legacy_vectorizer is not None
        )

    def _ensure_loaded(self) -> None:
        """Attempts to load model artifacts from disk if not previously attempted."""
        if self._load_attempted:
            return
        self._load_attempted = True

        local_hf_dir = self.models_dir / "fake_news_detector"
        if local_hf_dir.is_dir() and (local_hf_dir / "config.json").is_file():
            try:
                from transformers import AutoModelForSequenceClassification, AutoTokenizer
                import torch

                logger.info(f"Loading genuine DistilBERT fake news model from {local_hf_dir}")
                self._tokenizer = AutoTokenizer.from_pretrained(str(local_hf_dir))
                self._hf_model = AutoModelForSequenceClassification.from_pretrained(str(local_hf_dir))
                self._hf_model.eval()
                logger.info(f"Successfully loaded {HF_MODEL_ID} model with id2label: {self._hf_model.config.id2label}")
                return
            except Exception as e:
                logger.warning(f"Failed to load DistilBERT model from {local_hf_dir}: {e}")
                self._hf_model = None
                self._tokenizer = None

        # Check for legacy joblib model artifacts
        model_paths = [self.models_dir / "fake_news_model.joblib"]
        vectorizer_paths = [self.models_dir / "fake_news_vectorizer.joblib"]

        found_model = next((p for p in model_paths if p.is_file()), None)
        found_vec = next((p for p in vectorizer_paths if p.is_file()), None)

        if found_model and found_vec:
            try:
                import joblib

                self._legacy_model = joblib.load(found_model)
                self._legacy_vectorizer = joblib.load(found_vec)
                logger.info(f"Loaded legacy fake news model from {found_model}")
                return
            except Exception as e:
                logger.warning(f"Failed to load legacy model artifacts: {e}")
                self._legacy_model = None
                self._legacy_vectorizer = None

        logger.info("Fake news classification model artifacts not present on disk.")

    def set_model(self, model: Any, vectorizer: Any = None) -> None:
        """Injects model and vectorizer (primarily used for unit testing)."""
        if vectorizer is not None:
            self._legacy_model = model
            self._legacy_vectorizer = vectorizer
        else:
            self._hf_model = model
        self._load_attempted = True

    def _get_label_mapping(self) -> Tuple[int, int]:
        """
        Extracts the exact indices for real and fake classes from the model config.
        Never assumes index 0 is Real or Fake.
        """
        raw_id2label = getattr(self._hf_model.config, "id2label", {0: "fake", 1: "real"})
        # Normalize keys to ints
        mapping = {}
        for k, v in raw_id2label.items():
            idx = int(k) if str(k).isdigit() else k
            mapping[idx] = str(v).lower()

        real_idx = next((k for k, v in mapping.items() if "real" in v or "true" in v or "authentic" in v), 1)
        fake_idx = next((k for k, v in mapping.items() if "fake" in v or "false" in v or "misleading" in v), 0)
        return real_idx, fake_idx

    def detect_fakenews(self, raw_text: str) -> FakeNewsDetectResponse:
        """
        Implements POST /api/fakenews/detect.
        Evaluates news claim or text with the fine-tuned DistilBERT classifier.
        """
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
            raise ValidationError("Fake news detection model is currently unavailable on the server.")

        # Language inspection: detect Hindi / Devanagari script
        has_hindi = bool(re.search(r"[ऀ-ॿ]", cleaned))
        limitations: list[str] = []
        if has_hindi:
            limitations.append(
                "Model is specialized for English language text. Devanagari/Hindi input has limited classification reliability."
            )

        if self._hf_model is not None and self._tokenizer is not None:
            import torch

            inputs = self._tokenizer(
                cleaned,
                return_tensors="pt",
                truncation=True,
                max_length=512,
            )
            with torch.no_grad():
                logits = self._hf_model(**inputs).logits[0]
                probs = torch.softmax(logits, dim=-1)

            real_idx, fake_idx = self._get_label_mapping()
            prob_real = float(probs[real_idx].item())
            prob_fake = float(probs[fake_idx].item())

            if prob_fake > prob_real:
                api_label = "potentially_false"
                confidence = round(prob_fake, 2)
                explanation = (
                    f"DistilBERT evaluated this content and identified linguistic patterns and stylistic features "
                    f"predominantly found in misinformation datasets (model confidence: {confidence:.0%}). "
                    "This is a model-based classification; independent verification is still required before treating as fact."
                )
            else:
                api_label = "potentially_authentic"
                confidence = round(prob_real, 2)
                explanation = (
                    f"DistilBERT evaluated this content and identified structural and stylistic characteristics "
                    f"consistent with factual reporting (model confidence: {confidence:.0%}). "
                    "Independent verification is still required for critical claims."
                )

            if has_hindi:
                explanation += " Note: Input contains Hindi text which this English-specialized model does not natively support."

            return FakeNewsDetectResponse(
                success=True,
                label=api_label,
                confidence=confidence,
                model="distilbert-fake-news-detector-english",
                explanation=explanation,
                verification_status="unverified",
                limitations=limitations,
            )

        # Legacy model fallback
        cleaned_text = preprocess_text(cleaned)
        features = self._legacy_vectorizer.transform([cleaned_text])
        prediction = self._legacy_model.predict(features)[0]
        confidence = 0.85
        if hasattr(self._legacy_model, "predict_proba"):
            confidence = float(max(self._legacy_model.predict_proba(features)[0]))

        api_label = "potentially_false" if "fake" in str(prediction).lower() else "potentially_authentic"
        return FakeNewsDetectResponse(
            success=True,
            label=api_label,
            confidence=round(confidence, 2),
            model="legacy-fake-news-classifier",
            explanation="Model-based classification; independent verification is still required.",
            verification_status="unverified",
            limitations=limitations,
        )

    def analyze(self, raw_text: str) -> FakeNewsDetectionResult:
        """
        Processes news text for legacy /api/fake-news/analyze route.
        """
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
                    "No trained classification model is loaded right now, so we cannot produce a prediction. "
                    "We would rather show nothing than a guess. Cross-check the claim with trusted outlets "
                    "or a fact-checking organization in the meantime."
                ),
                recommendations=NEWS_RECOMMENDATIONS,
            )

        if self._hf_model is not None and self._tokenizer is not None:
            try:
                import torch

                inputs = self._tokenizer(
                    validated_text,
                    return_tensors="pt",
                    truncation=True,
                    max_length=512,
                )
                with torch.no_grad():
                    logits = self._hf_model(**inputs).logits[0]
                    probs = torch.softmax(logits, dim=-1)

                real_idx, fake_idx = self._get_label_mapping()
                prob_real = float(probs[real_idx].item())
                prob_fake = float(probs[fake_idx].item())

                if prob_fake > prob_real:
                    display_label = "Potentially Fake / Misleading"
                    confidence = round(prob_fake, 3)
                    explanation = (
                        f"DistilBERT evaluated this content and identified linguistic patterns and stylistic features "
                        f"predominantly found in misinformation datasets (confidence score: {confidence:.1%}). "
                        "Machine-learning classification is statistical guidance, not proof of factual accuracy."
                    )
                else:
                    display_label = "Consistent with Authentic News"
                    confidence = round(prob_real, 3)
                    explanation = (
                        f"DistilBERT evaluated this content and identified structural and linguistic characteristics "
                        f"consistent with factual reporting (confidence score: {confidence:.1%}). "
                        "Always independently confirm important assertions with primary sources."
                    )

                return FakeNewsDetectionResult(
                    success=True,
                    detector="fake_news",
                    status="completed",
                    model_available=True,
                    label=display_label,
                    confidence=confidence,
                    model="distilbert-fake-news-detector-english",
                    explanation=explanation,
                    recommendations=NEWS_RECOMMENDATIONS,
                )
            except Exception as err:
                logger.error(f"Inference error during DistilBERT analysis: {err}")
                return FakeNewsDetectionResult(
                    success=False,
                    detector="fake_news",
                    status="error",
                    model_available=True,
                    error="Model inference encountered an unexpected failure.",
                    explanation="Failed to complete DistilBERT model prediction on the provided text.",
                    recommendations=NEWS_RECOMMENDATIONS,
                )

        try:
            cleaned_text = preprocess_text(validated_text)
            features = self._legacy_vectorizer.transform([cleaned_text])
            prediction = self._legacy_model.predict(features)[0]

            confidence = None
            if hasattr(self._legacy_model, "predict_proba"):
                probabilities = self._legacy_model.predict_proba(features)[0]
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
            logger.error(f"Inference error during legacy fake news analysis: {err}")
            return FakeNewsDetectionResult(
                success=False,
                detector="fake_news",
                status="error",
                model_available=True,
                error="Model inference encountered an unexpected failure.",
                explanation="Failed to complete model prediction on the provided text.",
                recommendations=NEWS_RECOMMENDATIONS,
            )
