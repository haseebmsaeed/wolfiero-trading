"""Integration tests for health endpoints and logging."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    """Create a test client."""
    app = create_app()
    return TestClient(app)


def test_health_endpoint(client):
    """Test the /health endpoint returns ok."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_health_deep_endpoint(client):
    """Test the /health/deep endpoint."""
    response = client.get("/health/deep")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "strategy_version" in data


def test_health_deep_has_strategy_version(client):
    """Test that /health/deep reports the active strategy version."""
    response = client.get("/health/deep")
    assert response.status_code == 200
    data = response.json()
    assert data["strategy_version"] == "v1.0.0"


def test_request_id_in_response_headers(client):
    """Test that responses include X-Request-ID header."""
    response = client.get("/health")
    assert "X-Request-ID" in response.headers
    request_id = response.headers["X-Request-ID"]
    assert len(request_id) > 0


def test_custom_request_id_preserved(client):
    """Test that custom X-Request-ID is preserved."""
    custom_id = "custom-request-123"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.headers["X-Request-ID"] == custom_id


def test_error_includes_request_id(client):
    """Test that error responses include request ID."""
    response = client.get("/nonexistent")
    # 404 Not Found is expected
    assert response.status_code == 404
    # Request ID should still be in headers
    assert "X-Request-ID" in response.headers
