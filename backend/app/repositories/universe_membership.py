"""Firestore-backed UniverseMembership repository."""

from datetime import date

from google.cloud.firestore import AsyncClient


class UniverseMembershipRepository:
    """Firestore implementation: stores/retrieves UniverseMembership documents from universe_membership/{id}."""

    def __init__(self, db: AsyncClient):
        self.db = db
        self.collection = db.collection("universe_membership")

    async def create(self, data: dict[str, object]) -> str:
        """Create a new membership change record. Returns the auto-generated ID."""
        doc_ref = await self.collection.add(data)
        return str(doc_ref.id)

    async def list_by_symbol_date(self, symbol: str, refresh_date: date) -> list[dict[str, object]]:
        """List membership changes for a symbol on a specific date."""
        docs = self.collection.where("symbol", "==", symbol).where(
            "refresh_date", "==", refresh_date
        ).stream()
        results: list[dict[str, object]] = []
        async for doc in docs:
            data = doc.to_dict()
            if data:
                data["id"] = doc.id
                results.append(data)
        return results

    async def list_by_date(self, refresh_date: date) -> list[dict[str, object]]:
        """List all membership changes on a specific date."""
        docs = self.collection.where("refresh_date", "==", refresh_date).stream()
        results: list[dict[str, object]] = []
        async for doc in docs:
            data = doc.to_dict()
            if data:
                data["id"] = doc.id
                results.append(data)
        return results
