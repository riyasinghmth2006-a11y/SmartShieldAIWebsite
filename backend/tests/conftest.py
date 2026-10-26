"""Pytest shared fixtures and test client configuration."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    """Provides a synchronous FastAPI test client."""
    with TestClient(app) as test_client:
        yield test_client
