"""Shared Pydantic models and schemas for request/response validation."""

from typing import Any, Literal
from pydantic import BaseModel, Field


# ==========================================
# Base Detection Result Schema
# ==========================================

class BaseDetectionResult(BaseModel):
    """Common structure for all detector outputs."""
    success: bool = True
    detector: str
    status: Literal["completed", "model_unavailable", "error"] = "completed"
    model_available: bool = False
    explanation: str
    recommendations: list[str] = Field(default_factory=list)
    error: str | None = None


# ==========================================
# Scam / Spam Detection Schemas
# ==========================================

class ScamAnalyzeRequest(BaseModel):
    mode: Literal["message", "url"]
    content: str = Field(..., description="Message text or URL to evaluate")


class IndicatorHit(BaseModel):
    id: str
    label: str
    note: str


class ScamDetectionResult(BaseDetectionResult):
    detector: str = "scam"
    level: str  # "None found" | "Some signals" | "Multiple signals"
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    hits: list[IndicatorHit] = Field(default_factory=list)
    model: str | None = None
    confidence: float | None = None


class SpamDetectRequest(BaseModel):
    text: str = Field(..., description="Message text to analyze for spam")


class SpamDetectResponse(BaseModel):
    success: bool = True
    label: Literal["spam", "ham"]
    confidence: float
    reasons: list[str] = Field(default_factory=list)
    model: str
    hits: list[IndicatorHit] = Field(default_factory=list)
    level: str = "None found"
    error: str | None = None


# ==========================================
# Fake News Detection Schemas
# ==========================================

class FakeNewsAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=20, description="Article headline or body text")


class FakeNewsDetectionResult(BaseDetectionResult):
    detector: str = "fake_news"
    label: str | None = None
    confidence: float | None = None
    model: str | None = None


class FakeNewsDetectRequest(BaseModel):
    text: str = Field(..., min_length=1, description="News article or claim to analyze")


class FakeNewsDetectResponse(BaseModel):
    success: bool = True
    label: str  # "potentially_false" | "potentially_authentic"
    confidence: float
    model: str
    explanation: str
    verification_status: str = "unverified"
    limitations: list[str] = Field(default_factory=list)
    error: str | None = None


# ==========================================
# Deepfake Detection Schemas
# ==========================================

class DeepfakeDetectionResult(BaseDetectionResult):
    detector: str = "deepfake"
    label: str | None = None
    confidence: float | None = None
    model: str | None = None
    media_summary: dict[str, Any] | None = None


class DeepfakeDetectResponse(BaseModel):
    success: bool = True
    label: str
    confidence: float
    model: str
    explanation: str
    media_summary: dict[str, Any]
    verification_status: str = "unverified"
    error: str | None = None


# ==========================================
# Health & Status Schemas
# ==========================================

class HealthStatus(BaseModel):
    status: str = "ok"
    version: str
    models_configured: dict[str, bool]
