"""Rule-based heuristic scam and suspicious URL analysis service with ML spam detection."""

import os
import re
from pathlib import Path
from typing import Any, List

import joblib

from backend.config import MODELS_DIR
from backend.schemas import IndicatorHit, ScamDetectionResult, SpamDetectResponse
from backend.utils.logging import get_logger
from backend.validators import ValidationError, validate_scam_input

logger = get_logger("smartshield.scam_service")


# Indicator definition rules
HEURISTIC_RULES = [
    {
        "id": "urgency",
        "label": "Suspicious urgency",
        "regex": re.compile(
            r"\b(urgent|immediately|act now|within \d+ (hours?|minutes?|days?)|"
            r"final notice|suspended|expires?|last chance|immediate action required|"
            r"account locked|unauthorized access)\b",
            re.IGNORECASE,
        ),
        "note": "Pressure to act quickly is a common tactic to bypass rational skepticism.",
    },
    {
        "id": "sensitive",
        "label": "Requests for sensitive information",
        "regex": re.compile(
            r"\b(password|otp|pin|ssn|social security|card number|cvv|security code|"
            r"verify your (account|identity)|login details|credentials|bank details|"
            r"passcode|mother's maiden)\b",
            re.IGNORECASE,
        ),
        "note": "Legitimate institutions rarely request security credentials via unprompted messages.",
    },
    {
        "id": "payment",
        "label": "Unusual payment requests",
        "regex": re.compile(
            r"\b(gift ?cards?|wire transfer|crypto|bitcoin|western union|moneygram|"
            r"processing fee|pay (a )?fee|cash app|zelle|reload card)\b",
            re.IGNORECASE,
        ),
        "note": "Gift cards, cryptocurrency, and direct wire transfers are irreversible payment channels.",
    },
    {
        "id": "url",
        "label": "Suspicious URL characteristics",
        "regex": re.compile(
            r"(https?://\d{1,3}(?:\.\d{1,3}){3}|"  # IP address in URL
            r"bit\.ly|tinyurl\.com|t\.co/|is\.gd|cutt\.ly|"  # Shorteners
            r"https?://[^\s]*@|"  # Embedded credentials before host
            r"xn--|"  # Punycode spoofing
            r"\.(zip|top|xyz|click|work|gq|cf|ml)\b|"  # Risky / commonly abused TLDs
            r"https?://[^\s/]*-[^\s/]*-[^\s/]*\.)",  # Multi-hyphen lookalike domains
            re.IGNORECASE,
        ),
        "note": "Shortened, mismatched, or unusual link patterns can obscure the genuine destination.",
    },
]

RECOMMENDED_STEPS = [
    "Do not click links or share personal details yet.",
    "Contact the organization using a trusted phone number or verified site you already know.",
    "Report or delete the message if it remains suspicious.",
]

SPAM_REASON_PATTERNS = [
    (re.compile(r"\b(free|win|winner|won|prize|claim|reward|voucher|bonus|cash|selected|congratulations)\b", re.I), "Suspicious promotional or prize claim language"),
    (re.compile(r"\b(urgent|immediately|act now|suspended|locked|expire|hours|within)\b", re.I), "High-pressure urgency or threat of account suspension"),
    (re.compile(r"\b(password|pin|otp|verify|credentials|login|security)\b", re.I), "Solicitation of account security or credential verification"),
    (re.compile(r"\b(gift cards?|wire|crypto|bitcoin|fee|cash ?app|transfer)\b", re.I), "Request for non-standard, irreversible financial transactions"),
    (re.compile(r"(https?://|bit\.ly|tinyurl|\.xyz|\.top|\.click)", re.I), "Contains links or domain shorteners often associated with phishing"),
]


class ScamService:
    """Evaluates suspicious messages and URLs using trained ML models and heuristic pattern checks."""

    def __init__(self, models_dir: Path = MODELS_DIR):
        self.models_dir = Path(models_dir)
        self.spam_model: Any = None
        self.spam_vectorizer: Any = None
        self._load_attempted = False

    def _ensure_spam_model_loaded(self) -> None:
        if self._load_attempted:
            return
        self._load_attempted = True

        model_path = self.models_dir / "spam_detector_model.joblib"
        vec_path = self.models_dir / "spam_vectorizer.joblib"

        if model_path.is_file() and vec_path.is_file():
            try:
                self.spam_model = joblib.load(model_path)
                self.spam_vectorizer = joblib.load(vec_path)
                logger.info(f"Loaded trained spam classification model from {model_path}")
            except Exception as e:
                logger.warning(f"Failed to load spam detection model: {e}")
                self.spam_model = None
                self.spam_vectorizer = None
        else:
            logger.info("Spam model artifacts not found on disk.")

    def is_spam_model_available(self) -> bool:
        self._ensure_spam_model_loaded()
        return self.spam_model is not None and self.spam_vectorizer is not None

    def detect_spam(self, text: str) -> SpamDetectResponse:
        """
        Performs genuine ML inference on message text to classify as spam vs ham.
        """
        if not isinstance(text, str):
            raise ValidationError("Text must be a valid string.")

        cleaned = text.strip()
        if not cleaned:
            raise ValidationError("Please enter text to analyze.")
        if len(cleaned) < 3:
            raise ValidationError("Text is too short. Please provide at least 3 characters.")
        if len(cleaned) > 10000:
            raise ValidationError("Text exceeds maximum allowed length of 10,000 characters.")

        if not self.is_spam_model_available():
            raise ValidationError("Spam classification model artifact is currently unavailable.")

        # Extract features and predict
        features = self.spam_vectorizer.transform([cleaned])
        pred_label = self.spam_model.predict(features)[0]  # "spam" or "ham"

        # Calculate confidence
        confidence = 0.90
        if hasattr(self.spam_model, "predict_proba"):
            probs = self.spam_model.predict_proba(features)[0]
            classes = list(self.spam_model.classes_)
            if pred_label in classes:
                confidence = float(probs[classes.index(pred_label)])

        # Generate contextual reasons
        reasons: List[str] = []
        for pattern, reason_desc in SPAM_REASON_PATTERNS:
            if pattern.search(cleaned):
                reasons.append(reason_desc)

        if pred_label == "spam" and not reasons:
            reasons.append("Stylistic and vocabulary patterns align with bulk unsolicited messaging")
        elif pred_label == "ham" and not reasons:
            reasons.append("Linguistic patterns consistent with routine personal or professional communication")

        # Also evaluate heuristic indicators for rich UI breakdown
        hits: List[IndicatorHit] = []
        for rule in HEURISTIC_RULES:
            if rule["regex"].search(cleaned):
                hits.append(IndicatorHit(id=rule["id"], label=rule["label"], note=rule["note"]))

        hit_count = len(hits)
        level = "None found" if hit_count == 0 else "Some signals" if hit_count == 1 else "Multiple signals"

        return SpamDetectResponse(
            success=True,
            label=pred_label,
            confidence=round(confidence, 2),
            reasons=reasons,
            model="tfidf-logistic-regression-spam-v1",
            hits=hits,
            level=level,
        )

    def analyze(self, content: str, mode: str = "message") -> ScamDetectionResult:
        """
        Performs static heuristic analysis combined with ML classification if available.
        """
        validated_text = validate_scam_input(content, mode)

        logger.info(f"Analyzing {mode} with {len(validated_text)} characters")

        hits: List[IndicatorHit] = []

        for rule in HEURISTIC_RULES:
            matched = False

            # Test regex against content
            if rule["regex"].search(validated_text):
                matched = True

            # If URL mode and examining the URL rule, flag non-HTTPS or raw IP/insecure protocols
            if mode == "url" and rule["id"] == "url":
                cleaned_lower = validated_text.lower()
                if not cleaned_lower.startswith("https://"):
                    matched = True

            if matched:
                hits.append(
                    IndicatorHit(
                        id=rule["id"],
                        label=rule["label"],
                        note=rule["note"],
                    )
                )

        hit_count = len(hits)
        if hit_count == 0:
            level = "None found"
            risk_score = 0.0
            explanation = (
                "Our heuristic checks did not match known warning patterns. "
                "However, scams continuously evolve, so remain cautious with unsolicited contacts."
            )
        elif hit_count == 1:
            level = "Some signals"
            risk_score = 0.4
            explanation = (
                "The content contains one common warning characteristic. "
                "Verify the sender's identity through an independent, trusted channel before interacting."
            )
        else:
            level = "Multiple signals"
            risk_score = min(1.0, 0.4 + (hit_count * 0.2))
            explanation = (
                "The content contains multiple characteristics commonly associated with scam attempts. "
                "Exercise extreme caution and avoid interacting with links or requested actions."
            )

        model_name = None
        model_conf = None
        if mode == "message" and self.is_spam_model_available():
            try:
                spam_res = self.detect_spam(validated_text)
                model_name = spam_res.model
                model_conf = spam_res.confidence
                if spam_res.label == "spam":
                    risk_score = max(risk_score, spam_res.confidence)
                    level = "Multiple signals" if risk_score >= 0.7 else "Some signals"
                    explanation += f" Machine-learning classifier identified spam probability of {spam_res.confidence:.0%}."
            except Exception as e:
                logger.debug(f"ML spam check skipped during heuristic analysis: {e}")

        return ScamDetectionResult(
            success=True,
            detector="scam",
            status="completed",
            level=level,
            risk_score=risk_score,
            hits=hits,
            model_available=self.is_spam_model_available(),
            model=model_name,
            confidence=model_conf,
            explanation=explanation,
            recommendations=RECOMMENDED_STEPS,
        )
