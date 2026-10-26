"""Detection services for SmartShield AI."""

from backend.services.scam_service import ScamService
from backend.services.fake_news_service import FakeNewsService
from backend.services.deepfake_service import DeepfakeService

__all__ = ["ScamService", "FakeNewsService", "DeepfakeService"]
