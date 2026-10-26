"""Privacy-aware logging utilities for SmartShield AI."""

import logging
import re

# Redaction patterns for sensitive customer identifiers
REDACTION_PATTERNS = [
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[EMAIL_REDACTED]"),
    (re.compile(r"\b(?:\d[ -]*?){13,16}\b"), "[CARD_REDACTED]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN_REDACTED]"),
    (re.compile(r"(password|pin|otp)[:= ]+\S+", re.IGNORECASE), r"\1: [REDACTED]"),
]


class PrivacyFilter(logging.Filter):
    """Filters log records to redact common sensitive patterns."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, replacement in REDACTION_PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        return True


def get_logger(name: str = "smartshield") -> logging.Logger:
    """Configures and returns a privacy-preserving logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(PrivacyFilter())
        logger.addHandler(handler)
    return logger
