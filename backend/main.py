"""FastAPI application entry point for SmartShield AI."""

from fastapi import FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend import __version__
from backend.config import ALLOWED_ORIGINS, API_PREFIX
from backend.schemas import (
    DeepfakeDetectionResult,
    FakeNewsAnalyzeRequest,
    FakeNewsDetectionResult,
    HealthStatus,
    ScamAnalyzeRequest,
    ScamDetectionResult,
)
from backend.services.deepfake_service import DeepfakeService
from backend.services.fake_news_service import FakeNewsService
from backend.services.scam_service import ScamService
from backend.utils.logging import get_logger
from backend.validators import ValidationError

logger = get_logger("smartshield.api")

app = FastAPI(
    title="SmartShield AI Backend",
    description="Cybersecurity intelligence and media verification API.",
    version=__version__,
    docs_url=f"{API_PREFIX}/docs",
    openapi_url=f"{API_PREFIX}/openapi.json",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton service instances
scam_service = ScamService()
fake_news_service = FakeNewsService()
deepfake_service = DeepfakeService()


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Translates custom domain validation errors into standard 400 Bad Request responses."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "success": False, "error": str(exc)},
    )


# ==========================================
# Health Endpoint
# ==========================================

@app.get("/health", response_model=HealthStatus, tags=["Health"])
@app.get(f"{API_PREFIX}/health", response_model=HealthStatus, tags=["Health"])
async def health_check():
    """Returns system status and model readiness."""
    return HealthStatus(
        status="ok",
        version=__version__,
        models_configured={
            "scam_heuristic": True,
            "fake_news_model": fake_news_service.is_model_available(),
            "deepfake_model": deepfake_service.is_model_available(),
        },
    )


# ==========================================
# Scam Detection Route
# ==========================================

@app.post(
    f"{API_PREFIX}/scam/analyze",
    response_model=ScamDetectionResult,
    tags=["Scam Detection"],
)
async def analyze_scam(payload: ScamAnalyzeRequest):
    """
    Examines message text or suspicious URLs for urgency, sensitive data requests,
    unusual payment methods, and fraudulent URL characteristics.
    """
    try:
        result = scam_service.analyze(content=payload.content, mode=payload.mode)
        return result
    except ValidationError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as exc:
        logger.error(f"Unexpected error in scam analysis: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process scam analysis request.",
        )


# ==========================================
# Fake News Detection Route
# ==========================================

@app.post(
    f"{API_PREFIX}/fake-news/analyze",
    response_model=FakeNewsDetectionResult,
    tags=["Fake News Detection"],
)
async def analyze_fake_news(payload: FakeNewsAnalyzeRequest):
    """
    Evaluates news article headline or text with a trained ML model if installed.
    Returns 'model_unavailable' status when weights are absent.
    """
    try:
        result = fake_news_service.analyze(raw_text=payload.text)
        return result
    except ValidationError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as exc:
        logger.error(f"Unexpected error in fake news analysis: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process fake news analysis request.",
        )


# ==========================================
# Deepfake Detection Route
# ==========================================

@app.post(
    f"{API_PREFIX}/deepfake/analyze",
    response_model=DeepfakeDetectionResult,
    tags=["Deepfake Detection"],
)
async def analyze_deepfake(file: UploadFile = File(...)):
    """
    Validates uploaded image file bytes and checks for potential manipulation.
    Returns 'model_unavailable' status when no deepfake model is configured.
    """
    try:
        content = await file.read()
        filename = file.filename or "uploaded_image.png"
        result = deepfake_service.analyze_image(filename=filename, content=content)
        return result
    except ValidationError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as exc:
        logger.error(f"Unexpected error in deepfake analysis: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process deepfake image analysis request.",
        )
