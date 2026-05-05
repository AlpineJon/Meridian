"""Idempotent seeder — loads geographies, metric definitions, and snapshot
metrics into Postgres. Safe to re-run; uses ON CONFLICT upserts.

Run with:
    uv run python -m meridian.jobs.seed_db
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import psycopg
from psycopg.types.json import Json

from meridian.config import get_settings
from meridian.jobs.seed_data import GEOGRAPHIES, METRIC_DEFINITIONS, SNAPSHOTS, TRENDS


def _sync_url() -> str:
    return get_settings().database_url_sync.replace("postgresql+psycopg://", "postgresql://", 1)


def _months_back(end_iso: str, n: int) -> list[date]:
    """Return n end-of-month dates ending at end_iso (oldest first)."""
    end = datetime.fromisoformat(end_iso).date()
    out = []
    for i in range(n):
        # Walk back i months from end
        y, m = end.year, end.month
        for _ in range(i):
            m -= 1
            if m == 0:
                m = 12
                y -= 1
        # last day of month
        if m == 12:
            d = date(y + 1, 1, 1) - timedelta(days=1)
        else:
            d = date(y, m + 1, 1) - timedelta(days=1)
        out.append(d)
    out.reverse()
    return out


def upsert_geographies(cur: psycopg.Cursor) -> int:
    sql = """
        INSERT INTO geographies (geoid, level, name, state_code, parent_geoid,
                                 population, centroid_lon, centroid_lat)
        VALUES (%(geoid)s, %(level)s, %(name)s, %(state_code)s, %(parent_geoid)s,
                %(population)s, %(centroid_lon)s, %(centroid_lat)s)
        ON CONFLICT (geoid) DO UPDATE SET
            level = EXCLUDED.level,
            name = EXCLUDED.name,
            state_code = EXCLUDED.state_code,
            parent_geoid = EXCLUDED.parent_geoid,
            population = EXCLUDED.population,
            centroid_lon = EXCLUDED.centroid_lon,
            centroid_lat = EXCLUDED.centroid_lat,
            updated_at = now()
    """
    # Two-pass insert: parents first (no parent_geoid), then children
    parents = [g for g in GEOGRAPHIES if g["parent_geoid"] is None]
    children = [g for g in GEOGRAPHIES if g["parent_geoid"] is not None]
    cur.executemany(sql, parents)
    cur.executemany(sql, children)
    return len(parents) + len(children)


def upsert_metric_definitions(cur: psycopg.Cursor) -> int:
    sql = """
        INSERT INTO metric_definitions
            (metric_key, label, category, unit, source, refresh_cadence, description, formula)
        VALUES (%(metric_key)s, %(label)s, %(category)s, %(unit)s, %(source)s,
                %(refresh_cadence)s, %(description)s, %(formula)s)
        ON CONFLICT (metric_key) DO UPDATE SET
            label = EXCLUDED.label,
            category = EXCLUDED.category,
            unit = EXCLUDED.unit,
            source = EXCLUDED.source,
            refresh_cadence = EXCLUDED.refresh_cadence,
            description = EXCLUDED.description,
            formula = EXCLUDED.formula
    """
    cur.executemany(sql, METRIC_DEFINITIONS)
    return len(METRIC_DEFINITIONS)


def upsert_metrics(cur: psycopg.Cursor) -> int:
    sql = """
        INSERT INTO metrics (geoid, metric_key, period_end, period_kind, value, value_str, source)
        VALUES (%(geoid)s, %(metric_key)s, %(period_end)s, %(period_kind)s,
                %(value)s, %(value_str)s, %(source)s)
        ON CONFLICT (geoid, metric_key, period_end) DO UPDATE SET
            value = EXCLUDED.value,
            value_str = EXCLUDED.value_str,
            source = EXCLUDED.source,
            ingested_at = now()
    """
    rows: list[dict] = []

    # Source per category
    source_for_category = {
        "supply": {"realtor": ["active_listings", "new_listings_monthly", "new_listings_yoy",
                               "months_supply", "median_dom", "pct_price_reductions"],
                   "census_bps": ["permits_1unit_12mo", "permits_2to4_12mo", "permits_5plus_12mo", "permits_1unit_monthly"]},
        "pricing": "realtor",
        "demo_acs": ["population", "households", "median_household_income", "owner_occupied_pct",
                     "renter_occupied_pct", "median_home_value", "median_gross_rent",
                     "rent_to_income", "pop_growth_5y"],
        "demo_bls": ["unemployment_rate"],
        "composite": ["liquidity_score", "demand_pressure", "distress_indicator", "market_tier"],
    }

    def src_for(metric_key: str) -> str:
        if metric_key in source_for_category["composite"]:
            return "derived"
        if metric_key in source_for_category["demo_acs"]:
            return "census_acs"
        if metric_key in source_for_category["demo_bls"]:
            return "bls_laus"
        if metric_key in source_for_category["supply"]["census_bps"]:
            return "census_bps"
        return "realtor"

    for snap in SNAPSHOTS:
        end = datetime.fromisoformat(snap.period_end).date()
        for group in (snap.signals, snap.supply, snap.pricing, snap.demo):
            for k, v in group.items():
                rows.append(
                    {
                        "geoid": snap.geoid,
                        "metric_key": k,
                        "period_end": end,
                        "period_kind": "month",
                        "value": float(v) if not isinstance(v, str) else None,
                        "value_str": v if isinstance(v, str) else None,
                        "source": src_for(k),
                    }
                )
        # Rationales as text-valued metrics
        for kind, text in snap.rationale.items():
            rows.append(
                {
                    "geoid": snap.geoid,
                    "metric_key": f"rationale_{kind}",
                    "period_end": end,
                    "period_kind": "month",
                    "value": None,
                    "value_str": text,
                    "source": "derived",
                }
            )

    # Trends — emit one row per (geoid, metric_key, month)
    for (geoid, metric_key), values in TRENDS.items():
        months = _months_back(PERIOD_END_FROM_SNAPSHOT, len(values))
        for month_end, val in zip(months, values, strict=True):
            rows.append(
                {
                    "geoid": geoid,
                    "metric_key": metric_key,
                    "period_end": month_end,
                    "period_kind": "month",
                    "value": float(val),
                    "value_str": None,
                    "source": src_for(metric_key),
                }
            )

    cur.executemany(sql, rows)
    return len(rows)


def log_run(cur: psycopg.Cursor, started: datetime, rows_in: int, rows_upserted: int,
            status: str, error: str | None = None) -> None:
    cur.execute(
        """
        INSERT INTO ingestion_runs
            (source, started_at, finished_at, status, rows_in, rows_upserted, error, params)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        ("seed", started, datetime.utcnow(), status, rows_in, rows_upserted, error,
         Json({"job": "seed_db"})),
    )


PERIOD_END_FROM_SNAPSHOT = SNAPSHOTS[0].period_end


def main() -> None:
    started = datetime.utcnow()
    rows_in = len(GEOGRAPHIES) + len(METRIC_DEFINITIONS) + sum(
        len(s.signals) + len(s.supply) + len(s.pricing) + len(s.demo) + len(s.rationale)
        for s in SNAPSHOTS
    )
    print(f"Connecting to Supabase…")
    with psycopg.connect(_sync_url()) as conn:
        with conn.cursor() as cur:
            try:
                g = upsert_geographies(cur)
                print(f"  ✓ geographies: {g}")
                d = upsert_metric_definitions(cur)
                print(f"  ✓ metric_definitions: {d}")
                m = upsert_metrics(cur)
                print(f"  ✓ metrics (incl. trends): {m}")
                conn.commit()
                log_run(cur, started, rows_in, g + d + m, "success")
                conn.commit()
                print(f"\nDone in {(datetime.utcnow() - started).total_seconds():.1f}s")
            except Exception as e:
                conn.rollback()
                log_run(cur, started, rows_in, 0, "failed", str(e)[:2000])
                conn.commit()
                raise


if __name__ == "__main__":
    main()
