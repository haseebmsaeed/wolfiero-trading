"""FastAPI application factory and entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    """Application lifespan — startup and shutdown events."""
    # Startup
    settings = get_settings()
    settings.validate_strategy_weights()
    print(f"✓ Application started (env={settings.environment}, strategy={settings.strategy_version})")

    yield

    # Shutdown
    print("✓ Application shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Wolfiero Trading Agent",
        description="Decision-support system for swing trading",
        version="0.1.0",
        lifespan=lifespan,
    )

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
            "environment": settings.environment,
            "strategy_version": settings.strategy_version,
        }

    # Error handler
    @app.exception_handler(Exception)
    async def generic_exception_handler(request, exc):  # type: ignore
        """Global exception handler returning standard error envelope."""
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "detail": str(exc) if settings.environment == "development" else None,
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
        )

    return app


# Create the app instance
app = create_app()
