"""Ingest Census ACS 5-year demographics for all seeded geographies.

Run with:
    uv run python -m meridian.jobs.ingest_census_acs

Inserts/updates `metrics` rows with period_end = year-end of the ACS vintage.
Re-runnable; uses upsert.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import psycopg

from meridian.adapters.census_acs import DEFAULT_YEAR, CensusACSAdapter
from meridian.config import get_settings


# Subset of seeded geographies that have Census equivalents
MSA_GEOIDS = ["12940", "13820", "32820", "27140", "33660", "43340"]
STATE_GEOIDS = ["22", "01", "47", "28"]
PLACE_SPECS = [("22", "05000")]  # Baton Rouge city, LA
ZCTA_GEOIDS = ["70809", "70810", "70806", "70808", "70815"]


def _sync_url() -> str:
    return get_settings().database_url_sync.replace("postgresql+psycopg://", "postgresql://", 1)


async def run() -> None:
    started = datetime.now(timezone.utc)
    adapter = CensusACSAdapter()
    print(f"Census ACS ingest — vintage {DEFAULT_YEAR} (5-year ending {DEFAULT_YEAR})")
    print(f"Geographies: {len(MSA_GEOIDS)} MSAs, {len(STATE_GEOIDS)} states, "
          f"{len(PLACE_SPECS)} place, {len(ZCTA_GEOIDS)} ZCTAs")

    rows_in = 0
    upserted = 0
    err: str | None = None
    try:
        rows = await adapter.fetch(
            msa_geoids=MSA_GEOIDS,
            state_geoids=STATE_GEOIDS,
            place_specs=PLACE_SPECS,
            zcta_geoids=ZCTA_GEOIDS,
            year=DEFAULT_YEAR,
        )
        rows_in = len(rows)
        print(f"  ✓ fetched {rows_in} normalized metric rows from Census API")

        with psycopg.connect(_sync_url()) as conn:
            upserted = adapter.upsert_rows(conn, rows)
            print(f"  ✓ upserted {upserted} metric rows into Supabase")
            adapter.log_run(
                conn,
                started_at=started,
                finished_at=datetime.now(timezone.utc),
                status="success",
                rows_in=rows_in,
                rows_upserted=upserted,
                params={
                    "year": DEFAULT_YEAR,
                    "n_msas": len(MSA_GEOIDS),
                    "n_states": len(STATE_GEOIDS),
                    "n_places": len(PLACE_SPECS),
                    "n_zctas": len(ZCTA_GEOIDS),
                },
            )
            conn.commit()
        print(f"\nDone in {(datetime.now(timezone.utc) - started).total_seconds():.1f}s")
    except Exception as e:  # noqa: BLE001
        err = str(e)[:1500]
        print(f"  ✗ FAILED: {err}")
        with psycopg.connect(_sync_url()) as conn:
            adapter.log_run(
                conn,
                started_at=started,
                finished_at=datetime.now(timezone.utc),
                status="failed",
                rows_in=rows_in,
                rows_upserted=upserted,
                error=err,
                params={"year": DEFAULT_YEAR},
            )
            conn.commit()
        raise


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
