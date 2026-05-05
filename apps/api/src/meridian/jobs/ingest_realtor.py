"""Ingest Realtor.com inventory CSVs (county + metro). Run with:
    uv run python -m meridian.jobs.ingest_realtor
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import psycopg

from meridian.adapters.realtor import RealtorAdapter
from meridian.config import get_settings


def _sync_url() -> str:
    return get_settings().database_url_sync.replace("postgresql+psycopg://", "postgresql://", 1)


async def run() -> None:
    started = datetime.now(timezone.utc)
    adapter = RealtorAdapter()
    print("Realtor.com ingest…")

    rows = await adapter.fetch(levels=("county", "metro"))
    print(f"  fetched {len(rows):,} normalized rows")

    with psycopg.connect(_sync_url()) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT geoid FROM geographies")
            valid = {r[0] for r in cur.fetchall()}
        before = len(rows)
        rows = [r for r in rows if r.geoid in valid]
        skipped = before - len(rows)
        if skipped:
            print(f"  (skipped {skipped:,} rows for unknown geoids)")
        n = adapter.upsert_rows(conn, rows)
        adapter.log_run(
            conn, started_at=started, finished_at=datetime.now(timezone.utc),
            status="success", rows_in=len(rows), rows_upserted=n,
            params={"sources": ["county", "metro"]},
        )
        conn.commit()
    print(f"\n✓ {n:,} rows upserted in "
          f"{(datetime.now(timezone.utc) - started).total_seconds():.1f}s")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
