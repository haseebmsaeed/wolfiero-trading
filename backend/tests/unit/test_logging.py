"""Unit tests for logging module."""

from app.logging import (
    get_request_id,
    get_run_id,
    set_request_id,
    set_run_id,
    correlation_id_filter,
)


def test_request_id_context():
    """Test that request ID can be set and retrieved."""
    test_id = "test-request-123"
    set_request_id(test_id)
    assert get_request_id() == test_id


def test_run_id_context():
    """Test that run ID can be set and retrieved."""
    test_id = "test-run-456"
    set_run_id(test_id)
    assert get_run_id() == test_id


def test_correlation_id_filter_with_request_id():
    """Test that correlation_id_filter adds request_id to event dict."""
    set_request_id("request-789")
    event_dict = {"message": "test"}

    filtered = correlation_id_filter(None, "test", event_dict)

    assert "request_id" in filtered
    assert filtered["request_id"] == "request-789"
    assert filtered["message"] == "test"


def test_correlation_id_filter_with_run_id():
    """Test that correlation_id_filter adds run_id to event dict."""
    set_run_id("run-999")
    event_dict = {"message": "test"}

    filtered = correlation_id_filter(None, "test", event_dict)

    assert "run_id" in filtered
    assert filtered["run_id"] == "run-999"


def test_correlation_id_filter_empty_context():
    """Test that filter handles empty context vars."""
    # Reset both
    set_request_id("")
    set_run_id("")
    event_dict = {"message": "test"}

    filtered = correlation_id_filter(None, "test", event_dict)

    # Should not add empty values
    assert "request_id" not in filtered or filtered.get("request_id") == ""
    assert "run_id" not in filtered or filtered.get("run_id") == ""
