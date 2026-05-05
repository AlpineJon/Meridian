"""Bulk Census ACS ingest — one API call per level, covers ALL US geos.

Run with:
    uv run python -m meridian.jobs.ingest_census_acs_bulk

Far more efficient than per-geo calls (3 HTTP requests instead of 4,200).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import psycopg

from meridian.adapters.census_acs import DEFAULT_YEAR, CensusACSAdapter
from meridian.config import get_settings


def _sync_url() -> str:
    return get_settings().database_url_sync.replace("postgresql+psycopg://", "postgresql://", 1)


async def run() -> None:
    started = datetime.now(timezone.utc)
    adapter = CensusACSAdapter()
    print(f"Bulk Census ACS ingest — vintage {DEFAULT_YEAR}")

    print("  fetching all states…")
    state_rows = await adapter.fetch_all_states(DEFAULT_YEAR)
    print(f"    got {len(state_rows)} state metric rows")

    print("  fetching all MSAs (this takes ~30s for ~940 CBSAs)…")
    msa_rows = await adapter.fetch_all_msas(DEFAULT_YEAR)
    print(f"    got {len(msa_rows)} MSA metric rows")

    print("  fetching all counties (~3,200)…")
    county_rows = await adapter.fetch_all_counties(DEFAULT_YEAR)
    print(f"    got {len(county_rows)} county metric rows")

    print("  fetching all places (~32k cities/CDPs, may take ~60s)…")
    place_rows = await adapter.fetch_all_places(DEFAULT_YEAR)
    print(f"    got {len(place_rows)} place metric rows")

    print("  fetching all ZCTAs (~33k ZIPs, may take ~60s)…")
    zcta_rows = await adapter.fetch_all_zctas(DEFAULT_YEAR)
    print(f"    got {len(zcta_rows)} ZCTA metric rows")

    all_rows = state_rows + msa_rows + county_rows + place_rows + zcta_rows
    print(f"\n  upserting {len(all_rows)} total rows into Supabase…")

    with psycopg.connect(_sync_url()) as conn:
        # Filter out rows for geoids we don't have (FK violation otherwise)
        # Pull existing geoids in one shot
        with conn.cursor() as cur:
            cur.execute("SELECT geoid FROM geographies")
            valid_geoids = {r[0] for r in cur.fetchall()}
        before = len(all_rows)
        all_rows = [r for r in all_rows if r.geoid in valid_geoids]
        skipped = before - len(all_rows)
        if skipped:
            print(f"  (skipped {skipped} rows for unknown geoids)")

        upserted = adapter.upsert_rows(conn, all_rows)
        adapter.log_run(
            conn,
            started_at=started,
            finished_at=datetime.now(timezone.utc),
            status="success",
            rows_in=len(all_rows),
            rows_upserted=upserted,
            params={"year": DEFAULT_YEAR, "scope": "all_us_states_msas_counties"},
        )
        conn.commit()

    print(f"\n✓ {upserted} metric rows upserted in "
          f"{(datetime.now(timezone.utc) - started).total_seconds():.1f}s")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
