"""Rule-based heuristic scam and suspicious URL analysis service."""

import re
from typing import Any, List
from backend.schemas import IndicatorHit, ScamDetectionResult
from backend.utils.logging import get_logger
from backend.validators import validate_scam_input

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


class ScamService:
    """Evaluates suspicious messages and URLs using heuristic pattern checks."""

    def analyze(self, content: str, mode: str = "message") -> ScamDetectionResult:
        """
        Performs static heuristic analysis without executing content or resolving URLs.
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

        return ScamDetectionResult(
            success=True,
            detector="scam",
            status="completed",
            level=level,
            risk_score=risk_score,
            hits=hits,
            model_available=False,  # Transparent: this is rule-based, not an ML classifier
            explanation=explanation,
            recommendations=RECOMMENDED_STEPS,
        )
