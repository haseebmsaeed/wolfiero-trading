"""Firestore client factory and configuration."""

import os
from functools import lru_cache

from google.cloud.firestore import AsyncClient

from app.config import get_settings


@lru_cache(maxsize=1)
def get_firestore_client() -> AsyncClient:
    """Get or create a cached Firestore client.

    Respects the FIRESTORE_EMULATOR_HOST environment variable for local development.
    """
    settings = get_settings()

    client = AsyncClient(project=settings.gcp_project_id)

    # Emulator mode: if FIRESTORE_EMULATOR_HOST is set, the Google Cloud SDK
    # automatically routes the client to the local emulator instead of the real service.
    # This is handled transparently by the google.cloud.firestore_async library.
    if os.getenv("FIRESTORE_EMULATOR_HOST"):
        # Just for logging/debugging — actual routing is handled by the library.
        pass

    return client
