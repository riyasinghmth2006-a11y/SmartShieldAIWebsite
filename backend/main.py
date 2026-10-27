
"""FastAPI application entry point for SmartShield AI."""

from fastapi import FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend import __version__
from backend.config import ALLOWED_ORIGINS, API_PREFIX
from backend.schemas import (
    DeepfakeDetectResponse,
    DeepfakeDetectionResult,
    FakeNewsAnalyzeRequest,
    FakeNewsDetectRequest,
    FakeNewsDetectResponse,
    FakeNewsDetectionResult,
    HealthStatus,
    ScamAnalyzeRequest,
    ScamDetectionResult,
    SpamDetectRequest,
    SpamDetectResponse,
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
    allow_origin_regex=(
        r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$"
        r"|^https?://ais-.*\.run\.app$"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton service instances
scam_service = ScamService()
fake_news_service = FakeNewsService()
deepfake_service = DeepfakeService()


@app.exception_handler(ValidationError)
async def validation_exception_handler(
    request: Request,
    exc: ValidationError,
):
    """Convert validation errors into HTTP 400 responses."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": str(exc),
            "success": False,
            "error": str(exc),
        },
    )


# ==========================================
# Health Endpoints
# ==========================================

@app.get("/health", response_model=HealthStatus, tags=["Health"])
@app.get(f"{API_PREFIX}/health", response_model=HealthStatus, tags=["Health"])
async def health_check():
    """
    Lightweight health check.
    Does not explicitly call model-availability methods.
    """
    return HealthStatus(
        status="ok",
        version=__version__,
        models_configured={
            "scam_heuristic": True,
            "spam_model": False,
            "fake_news_model": False,
            "deepfake_model": False,
        },
    )


# ==========================================
# Spam & Scam Detection Routes
# ==========================================

@app.post(
    f"{API_PREFIX}/spam/detect",
    response_model=SpamDetectResponse,
    tags=["Spam Detection"],
)
async def detect_spam(payload: SpamDetectRequest):
    """Perform spam classification."""
    try:
        return scam_service.detect_spam(text=payload.text)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception:
        logger.exception("Unexpected error in spam detection")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process spam detection request.",
        )


@app.post(
    f"{API_PREFIX}/scam/analyze",
    response_model=ScamDetectionResult,
    tags=["Scam Detection"],
)
async def analyze_scam(payload: ScamAnalyzeRequest):
    """Analyze suspicious messages and URLs."""
    try:
        return scam_service.analyze(
            content=payload.content,
            mode=payload.mode,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception:
        logger.exception("Unexpected error in scam analysis")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process scam analysis request.",
        )


# ==========================================
# Fake News Detection Routes
# ==========================================

@app.post(
    f"{API_PREFIX}/fakenews/detect",
    response_model=FakeNewsDetectResponse,
    tags=["Fake News Detection"],
)
async def detect_fakenews(payload: FakeNewsDetectRequest):
    """Evaluate news text using the configured classifier."""
    try:
        return fake_news_service.detect_fakenews(raw_text=payload.text)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception:
        logger.exception("Unexpected error in fake news detection")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process fake news detection request.",
        )


@app.post(
    f"{API_PREFIX}/fake-news/analyze",
    response_model=FakeNewsDetectionResult,
    tags=["Fake News Detection"],
)
async def analyze_fake_news(payload: FakeNewsAnalyzeRequest):
    """Analyze news text using the legacy-compatible route."""
    try:
        return fake_news_service.analyze(raw_text=payload.text)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception:
        logger.exception("Unexpected error in fake news analysis")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process fake news analysis request.",
        )


# ==========================================
# Deepfake Detection Routes
# ==========================================

@app.post(
    f"{API_PREFIX}/deepfake/detect",
    response_model=DeepfakeDetectResponse,
    tags=["Deepfake Detection"],
)
async def detect_deepfake(file: UploadFile = File(...)):
    """Analyze an uploaded image for potential manipulation."""
    try:
        content = await file.read()
        filename = file.filename or "uploaded_image.png"

        return deepfake_service.detect_deepfake(
            filename=filename,
            content=content,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception:
        logger.exception("Unexpected error in deepfake detection")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process deepfake image detection request.",
        )


@app.post(
    f"{API_PREFIX}/deepfake/analyze",
    response_model=DeepfakeDetectionResult,
    tags=["Deepfake Detection"],
)
async def analyze_deepfake(file: UploadFile = File(...)):
    """Analyze an image through the legacy-compatible route."""
    try:
        content = await file.read()
        filename = file.filename or "uploaded_image.png"

        return deepfake_service.analyze_image(
            filename=filename,
            content=content,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception:
        logger.exception("Unexpected error in deepfake analysis")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process deepfake image analysis request.",
        )
