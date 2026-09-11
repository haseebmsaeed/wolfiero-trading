"""Database session management."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings


def get_engine():
    """Create async SQLAlchemy engine."""
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.environment == "development",
        future=True,
    )


def get_session_factory():
    """Create async session factory."""
    engine = get_engine()
    return sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db() -> AsyncSession:  # type: ignore
    """FastAPI dependency for getting a database session."""
    factory = get_session_factory()
    async with factory() as session:
        yield session
