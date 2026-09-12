"""Firestore-backed StrategyVersion repository."""


from google.cloud.firestore import AsyncClient


class StrategyVersionRepository:
    """Firestore implementation: stores/retrieves StrategyVersion documents from strategy_versions/{version}."""

    def __init__(self, db: AsyncClient):
        self.db = db
        self.collection = db.collection("strategy_versions")

    async def get(self, version: str) -> dict[str, object] | None:
        """Get a strategy version by version string."""
        doc = await self.collection.document(version).get()
        if doc.exists:
            data = doc.to_dict()
            if data:
                data["version"] = version
                return data
        return None

    async def create(self, version: str, data: dict) -> None:
        """Create a new strategy version (fails if already exists)."""
        doc = await self.collection.document(version).get()
        if doc.exists:
            raise ValueError(f"Strategy version {version} already exists")
        await self.collection.document(version).set(data)

    async def list_all(self) -> list[dict[str, object]]:
        """List all strategy versions (all documents in collection)."""
        docs = self.collection.stream()
        results: list[dict[str, object]] = []
        async for doc in docs:
            data = doc.to_dict()
            if data:
                data["version"] = doc.id
                results.append(data)
        return results
