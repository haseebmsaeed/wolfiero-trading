"""Firestore-backed UniverseMembership repository."""

from datetime import date
from typing import Optional

from google.cloud.firestore import AsyncClient

from app.models import UniverseMembership


class UniverseMembershipRepository:
    """Firestore implementation: stores/retrieves UniverseMembership documents from universe_membership/{id}."""

    def __init__(self, db: AsyncClient):
        self.db = db
        self.collection = db.collection("universe_membership")

    async def create(self, data: dict) -> str:
        """Create a new membership change record. Returns the auto-generated ID."""
        doc_ref = await self.collection.add(data)
        return doc_ref.id

    async def list_by_symbol_date(self, symbol: str, refresh_date: date) -> list[dict]:
        """List membership changes for a symbol on a specific date."""
        docs = await self.collection.where("symbol", "==", symbol).where(
            "refresh_date", "==", refresh_date
        ).stream()
        results = []
        async for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)
        return results

    async def list_by_date(self, refresh_date: date) -> list[dict]:
        """List all membership changes on a specific date."""
        docs = await self.collection.where("refresh_date", "==", refresh_date).stream()
        results = []
        async for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)
        return results
