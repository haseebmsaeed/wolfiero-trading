"""Structured logging configuration with correlation IDs."""

import contextvars
import logging
import sys
import uuid
from typing import Any

import structlog
from structlog.types import FilteringBoundLogger

# Correlation ID context var
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)
run_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "run_id", default=""
)


def get_request_id() -> str:
    """Get the current request ID."""
    return request_id_ctx.get()


def set_request_id(request_id: str) -> None:
    """Set the current request ID."""
    request_id_ctx.set(request_id)


def get_run_id() -> str:
    """Get the current run ID (for background jobs)."""
    return run_id_ctx.get()


def set_run_id(run_id: str) -> None:
    """Set the current run ID."""
    run_id_ctx.set(run_id)


def correlation_id_filter(
    logger: Any, name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add correlation ID to every log line."""
    request_id = get_request_id()
    run_id = get_run_id()

    if request_id:
        event_dict["request_id"] = request_id
    if run_id:
        event_dict["run_id"] = run_id

    return event_dict


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structlog with JSON output.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Configure structlog
    structlog.configure(
        processors=[
            correlation_id_filter,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure root logger
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    # Get structlog logger
    logger = structlog.get_logger()
    logger.info(
        "logging_configured",
        level=log_level,
    )


def get_logger(name: str = __name__) -> FilteringBoundLogger:
    """Get a structlog logger."""
    return structlog.get_logger(name)
