"""Smoke tests to verify basic project structure."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


def test_app_creation():
    """Test that the app can be created without errors."""
    app = create_app()
    assert app is not None
    assert app.title == "Wolfiero Trading Agent"


def test_health_endpoint():
    """Test the /health endpoint."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_deep_endpoint():
    """Test the /health/deep endpoint."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/health/deep")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert "strategy_version" in data
