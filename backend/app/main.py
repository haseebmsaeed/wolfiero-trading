"""FastAPI application factory and entry point."""

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import stocks, admin, scanner
from app.config import get_settings
from app.logging import get_logger, set_request_id, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    """Application lifespan — startup and shutdown events."""
    # Startup
    settings = get_settings()
    setup_logging(settings.log_level)
    settings.validate_strategy_weights()
    logger.info(
        "application_started",
        strategy_version=settings.strategy_version,
    )

    yield

    # Shutdown
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Wolfiero Trading Agent",
        description="Decision-support system for swing trading",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Add CORS middleware (restrictive)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware: correlation ID injection and request logging
    @app.middleware("http")
    async def correlation_id_middleware(request: Request, call_next):  # type: ignore
        """Add correlation ID to all requests and log them."""
        # Get or create request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        set_request_id(request_id)
        request.state.request_id = request_id

        # Log request
        start_time = time.time()
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            request_id=request_id,
        )

        # Call next middleware/handler
        response = await call_next(request)

        # Log response
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            request_id=request_id,
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        return response

    # Health endpoints
    @app.get("/health")
    async def health() -> dict:  # type: ignore
        """Liveness check."""
        return {"status": "ok"}

    @app.get("/health/deep")
    async def health_deep() -> dict:  # type: ignore
        """Deep health check (DB, providers, etc.)."""
        return {
            "status": "healthy",
            "strategy_version": settings.strategy_version,
        }

    # Mount routers
    app.include_router(stocks.router)
    app.include_router(admin.router)
    app.include_router(scanner.router)

    # Error handler
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):  # type: ignore
        """Global exception handler returning standard error envelope."""
        request_id = getattr(request.state, "request_id", None)
        logger.error(
            "unhandled_exception",
            error=str(exc),
            error_type=type(exc).__name__,
            request_id=request_id,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "detail": None,
                    "request_id": request_id,
                }
            },
        )

    return app


# Create the app instance
app = create_app()
