"""Firestore-backed Candidate repository."""

from datetime import date

from google.cloud.firestore import AsyncClient


class CandidateRepository:
    """Firestore implementation: stores/retrieves Candidate documents from scan_runs/{run_id}/candidates/{symbol}."""

    def __init__(self, db: AsyncClient):
        self.db = db
        self.scan_runs_collection = db.collection("scan_runs")

    def _subcollection_ref(self, run_id: str):
        """Return the candidates subcollection reference for a run."""
        return self.scan_runs_collection.document(run_id).collection("candidates")

    async def create_many(self, run_id: str, candidates: list[dict]) -> None:
        """Create multiple candidate records for a run.

        Uses .create() semantics (fails on duplicate) to enforce immutability.
        """
        subcoll = self._subcollection_ref(run_id)
        batch = self.db.batch()

        for cand in candidates:
            symbol = cand["symbol"]
            doc = await subcoll.document(symbol).get()
            if doc.exists:
                raise ValueError(f"Candidate {run_id}_{symbol} already exists (immutable)")
            batch.set(subcoll.document(symbol), cand)

        await batch.commit()

    async def get(self, run_id: str, symbol: str) -> dict | None:
        """Get a single candidate by run_id and symbol."""
        doc = await self._subcollection_ref(run_id).document(symbol).get()
        if doc.exists:
            data = doc.to_dict()
            data["run_id"] = run_id
            data["symbol"] = symbol
            return data
        return None

    async def list_by_run(
        self, run_id: str, include_vetoed: bool = False, limit: int = 20
    ) -> list[dict]:
        """List candidates for a run, optionally filtering vetoed status."""
        query = self._subcollection_ref(run_id)
        if not include_vetoed:
            query = query.where("is_vetoed", "==", False)
        query = query.order_by("rank")
        query = query.limit(limit)

        docs = await query.stream()
        results = []
        async for doc in docs:
            data = doc.to_dict()
            data["run_id"] = run_id
            data["symbol"] = doc.id
            results.append(data)
        return results

    async def list_by_date(
        self, trade_date: date, include_vetoed: bool = False, limit: int = 20
    ) -> list[dict]:
        """List candidates for a trade date (searches all runs on that date)."""
        scan_runs = await self.scan_runs_collection.where(
            "trade_date", "==", trade_date
        ).stream()

        results = []
        async for run_doc in scan_runs:
            run_id = run_doc.id
            query = self._subcollection_ref(run_id)
            if not include_vetoed:
                query = query.where("is_vetoed", "==", False)
            query = query.order_by("rank")

            cands = await query.stream()
            async for cand_doc in cands:
                data = cand_doc.to_dict()
                data["run_id"] = run_id
                data["symbol"] = cand_doc.id
                results.append(data)

        results.sort(key=lambda c: c.get("rank", 999))
        return results[:limit]
