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
    status: Literal["completed", "model_unavailable", "error"]
    model_available: bool = False
    explanation: str
    recommendations: list[str] = Field(default_factory=list)
    error: str | None = None


# ==========================================
# Scam Detection Schemas
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


# ==========================================
# Fake News Detection Schemas
# ==========================================

class FakeNewsAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=20, description="Article headline or body text")


class FakeNewsDetectionResult(BaseDetectionResult):
    detector: str = "fake_news"
    label: str | None = None
    confidence: float | None = None


# ==========================================
# Deepfake Detection Schemas
# ==========================================

class DeepfakeDetectionResult(BaseDetectionResult):
    detector: str = "deepfake"
    label: str | None = None
    confidence: float | None = None
    media_summary: dict[str, Any] | None = None


# ==========================================
# Health & Status Schemas
# ==========================================

class HealthStatus(BaseModel):
    status: str = "ok"
    version: str
    models_configured: dict[str, bool]
