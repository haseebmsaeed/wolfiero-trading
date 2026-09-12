"""Firestore-backed Stock repository."""


from google.cloud.firestore import AsyncClient


class StockRepository:
    """Firestore implementation: stores/retrieves Stock documents from stocks/{symbol}."""

    def __init__(self, db: AsyncClient):
        self.db = db
        self.collection = db.collection("stocks")

    async def get_by_symbol(self, symbol: str) -> dict[str, object] | None:
        """Get a stock document by symbol (the document ID)."""
        doc = await self.collection.document(symbol).get()
        if doc.exists:
            data = doc.to_dict()
            if data:
                data["symbol"] = symbol
                return data
        return None

    async def list_active(self) -> list[dict[str, object]]:
        """List all stocks where is_active=True."""
        docs = self.collection.where("is_active", "==", True).stream()
        results: list[dict[str, object]] = []
        async for doc in docs:
            data = doc.to_dict()
            if data:
                data["symbol"] = doc.id
                results.append(data)
        return results

    async def list_universe(self) -> list[dict[str, object]]:
        """List all stocks where is_active=True AND in_universe=True."""
        docs = self.collection.where("is_active", "==", True).where(
            "in_universe", "==", True
        ).stream()
        results: list[dict[str, object]] = []
        async for doc in docs:
            data = doc.to_dict()
            if data:
                data["symbol"] = doc.id
                results.append(data)
        return results

    async def upsert(self, symbol: str, data: dict[str, object]) -> None:
        """Create or update a stock document (merge semantics)."""
        await self.collection.document(symbol).set(data, merge=True)

    async def update_in_universe_batch(
        self, symbols_to_add: set[str], symbols_to_remove: set[str]
    ) -> None:
        """Batch update in_universe flag for multiple symbols."""
        batch = self.db.batch()
        for symbol in symbols_to_add:
            batch.update(self.collection.document(symbol), {"in_universe": True})
        for symbol in symbols_to_remove:
            batch.update(self.collection.document(symbol), {"in_universe": False})
        await batch.commit()
