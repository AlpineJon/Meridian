"""Source adapter pattern.

Every external data source (Census ACS, Census BPS, BLS LAUS, FRED, Realtor,
Zillow) implements `BaseAdapter`. The adapter does three things:

  1. Fetch raw data from upstream (with caching + retry)
  2. Normalize it into `FetchedRow` records (one per metric per period per geo)
  3. Caller upserts via `upsert_rows()` into the metrics table

Adding a new source = adding a new adapter file. The pipeline doesn't change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

import psycopg
from psycopg.types.json import Json

from meridian.models.metric import SourceName


@dataclass(frozen=True, slots=True)
class FetchedRow:
    """Normalized row ready to upsert into `metrics`."""

    geoid: str
    metric_key: str
    period_end: date
    period_kind: str  # day | week | month | quarter | year
    value: float | None = None
    value_str: str | None = None


class BaseAdapter(ABC):
    """Subclass and implement `fetch()`. The runner calls fetch + upsert_rows."""

    source: SourceName  # must be set by subclass

    @abstractmethod
    async def fetch(self, **params) -> list[FetchedRow]:
        """Fetch upstream data and return normalized rows.

        Implementations are responsible for caching at the network layer
        (e.g. Redis-cached httpx responses) so that re-running a job is cheap.
        """
        ...

    BATCH_SIZE = 2000
    BATCH_DELAY_SEC = 0.25  # gentle on free-tier Supabase compute

    def upsert_rows(self, conn: psycopg.Connection, rows: Iterable[FetchedRow]) -> int:
        """Bulk upsert rows into `metrics`. Batched + commits per batch
        so a 1M-row payload doesn't blow the Supabase pooler connection."""
        rows = list(rows)
        if not rows:
            return 0
        sql = """
            INSERT INTO metrics
                (geoid, metric_key, period_end, period_kind, value, value_str, source)
            VALUES
                (%(geoid)s, %(metric_key)s, %(period_end)s, %(period_kind)s,
                 %(value)s, %(value_str)s, %(source)s)
            ON CONFLICT (geoid, metric_key, period_end) DO UPDATE SET
                value = EXCLUDED.value,
                value_str = EXCLUDED.value_str,
                source = EXCLUDED.source,
                ingested_at = now()
        """

        def _to_param(r: FetchedRow) -> dict:
            return {
                "geoid": r.geoid,
                "metric_key": r.metric_key,
                "period_end": r.period_end,
                "period_kind": r.period_kind,
                "value": r.value,
                "value_str": r.value_str,
                "source": self.source.value,
            }

        import time
        total = 0
        n = len(rows)
        for i in range(0, n, self.BATCH_SIZE):
            chunk = rows[i : i + self.BATCH_SIZE]
            params = [_to_param(r) for r in chunk]
            with conn.cursor() as cur:
                cur.executemany(sql, params)
            conn.commit()
            total += len(chunk)
            if (i // self.BATCH_SIZE) % 20 == 0 and i > 0:
                pct = 100 * total / n
                print(f"    ... {total:,}/{n:,} ({pct:.0f}%)")
            if self.BATCH_DELAY_SEC and i + self.BATCH_SIZE < n:
                time.sleep(self.BATCH_DELAY_SEC)
        return total

    def log_run(
        self,
        conn: psycopg.Connection,
        started_at,
        finished_at,
        status: str,
        rows_in: int = 0,
        rows_upserted: int = 0,
        error: str | None = None,
        params: dict | None = None,
    ) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ingestion_runs
                    (source, started_at, finished_at, status, rows_in, rows_upserted, error, params)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    self.source.value,
                    started_at,
                    finished_at,
                    status,
                    rows_in,
                    rows_upserted,
                    error,
                    Json(params or {}),
                ),
            )
