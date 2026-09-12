"""Firestore-backed PriceHistory repository."""

from datetime import date
from typing import Optional

from google.cloud.firestore import AsyncClient
import pandas as pd

from app.models import PriceHistory


class PriceHistoryRepository:
    """Firestore implementation: stores/retrieves price bars from stocks/{symbol}/price_history/{trade_date}."""

    def __init__(self, db: AsyncClient):
        self.db = db
        self.stocks_collection = db.collection("stocks")

    def _subcollection_ref(self, symbol: str):
        """Return the price_history subcollection reference for a symbol."""
        return self.stocks_collection.document(symbol).collection("price_history")

    async def get_bars(
        self, symbol: str, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """Fetch bars for a symbol, optionally filtered by date range. Returns DataFrame with trade_date index."""
        query = self._subcollection_ref(symbol)
        if start_date:
            query = query.where("trade_date", ">=", start_date)
        if end_date:
            query = query.where("trade_date", "<=", end_date)

        query = query.order_by("trade_date")
        docs = await query.stream()

        records = []
        async for doc in docs:
            data = doc.to_dict()
            data["trade_date"] = doc.id  # Doc ID is the trade_date as a date string
            records.append(data)

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
        df.set_index("trade_date", inplace=True)
        return df

    async def upsert_batch(self, symbol: str, bars: pd.DataFrame) -> None:
        """Batch upsert bars for a symbol. bars is a DataFrame with trade_date index."""
        subcoll = self._subcollection_ref(symbol)
        batch = self.db.batch()

        for trade_date, row in bars.iterrows():
            doc_id = trade_date.strftime("%Y-%m-%d") if hasattr(trade_date, "strftime") else str(trade_date)
            data = {
                "trade_date": trade_date if isinstance(trade_date, date) else pd.Timestamp(trade_date).date(),
                "open": row.get("open"),
                "high": row.get("high"),
                "low": row.get("low"),
                "close": row.get("close"),
                "volume": row.get("volume"),
                "adjusted": row.get("adjusted", True),
                "source": row.get("source"),
                "ingested_at": row.get("ingested_at"),
            }
            batch.set(subcoll.document(doc_id), data, merge=True)

        await batch.commit()

    async def count(self, symbol: str) -> int:
        """Count total bars for a symbol."""
        aggregate_query = await self._subcollection_ref(symbol).count().get()
        return aggregate_query[0][0].value

    async def latest_date(self, symbol: str) -> Optional[date]:
        """Get the most recent trade_date for a symbol."""
        docs = await self._subcollection_ref(symbol).order_by("trade_date", direction="DESCENDING").limit(1).stream()
        async for doc in docs:
            if doc.exists:
                trade_date = doc.get("trade_date")
                return trade_date if isinstance(trade_date, date) else pd.Timestamp(trade_date).date()
        return None
