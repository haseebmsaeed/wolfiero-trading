"""Firestore-backed ScanRun repository."""

from datetime import date

from google.cloud.firestore import AsyncClient


class ScanRunRepository:
    """Firestore implementation: stores/retrieves ScanRun documents from scan_runs/{run_id}."""

    def __init__(self, db: AsyncClient):
        self.db = db
        self.collection = db.collection("scan_runs")

    async def create(self, run_id: str, data: dict) -> None:
        """Create a new scan run (fails if run_id already exists)."""
        doc = await self.collection.document(run_id).get()
        if doc.exists:
            raise ValueError(f"Scan run {run_id} already exists")
        await self.collection.document(run_id).set(data)

    async def get(self, run_id: str) -> dict | None:
        """Get a scan run by run_id."""
        doc = await self.collection.document(run_id).get()
        if doc.exists:
            data = doc.to_dict()
            data["run_id"] = run_id
            return data
        return None

    async def get_by_date_version(self, trade_date: date, version: str) -> dict | None:
        """Get the scan run for a specific date and strategy version."""
        docs = await self.collection.where("trade_date", "==", trade_date).where(
            "strategy_version", "==", version
        ).limit(1).stream()
        async for doc in docs:
            if doc.exists:
                data = doc.to_dict()
                data["run_id"] = doc.id
                return data
        return None
