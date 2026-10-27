"""Configuration settings for SmartShield AI backend service."""

import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"

# Server configuration
API_PREFIX = "/api"
HOST = os.getenv("SMARTSHIELD_HOST", "0.0.0.0")
PORT = int(os.getenv("SMARTSHIELD_PORT", "8001"))

# Allowed CORS origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8443",
    "http://127.0.0.1:8443",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8001",
    "http://127.0.0.1:8001",
]

# Validation limits
MIN_SCAM_TEXT_LENGTH = 3
MAX_SCAM_TEXT_LENGTH = 5000

MIN_NEWS_TEXT_LENGTH = 20
MAX_NEWS_TEXT_LENGTH = 20000

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
