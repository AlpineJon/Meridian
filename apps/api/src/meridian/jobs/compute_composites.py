"""Compute composite credit signals from raw upstream metrics.

Reads the latest values of supply + pricing metrics per geography, computes
the four signals (Liquidity / Demand / Distress / Tier), and upserts them as
`source=derived` metric rows.

Formulas (also documented in METRICS.md):

  months_supply ≈ active_listings / pending_sales (proxy when closed-sales
                  pace isn't published; matches Realtor.com inventory data)

  liquidity_score = 100 *
      (0.5 * (1 - clamp(months_supply / 8, 0, 1))      # tightness
     + 0.5 * (1 - clamp(median_dom    / 120, 0, 1)))    # speed of sale

  demand_pressure = 100 *
      (0.6 * sale_price_yoy        # price momentum
     + 0.4 * (0 - active_listings_yoy))   # inventory shift (inverse)

  distress_indicator = 100 * pct_price_reductions

  market_tier:
      A: liquidity >= 70 AND distress <= 30
      B: liquidity >= 50 AND distress <= 50
      C: liquidity >= 35
      D: otherwise

Run with:
    uv run python -m meridian.jobs.compute_composites
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

import psycopg
from psycopg.types.json import Json

from meridian.config import get_settings


def _sync_url() -> str:
    return get_settings().database_url_sync.replace("postgresql+psycopg://", "postgresql://", 1)


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _tier(liq: float | None, distress: float | None) -> str | None:
    if liq is None or distress is None:
        return None
    if liq >= 70 and distress <= 30:
        return "A"
    if liq >= 50 and distress <= 50:
        return "B"
    if liq >= 35:
        return "C"
    return "D"


def main() -> None:
    started = datetime.now(timezone.utc)
    print("Computing composite credit signals…")

    with psycopg.connect(_sync_url()) as conn:
        # ---- pull latest value per (geoid, metric_key) ----
        latest: dict[str, dict[str, tuple[float, "datetime"]]] = defaultdict(dict)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (geoid, metric_key)
                       geoid, metric_key, value, period_end
                FROM metrics
                WHERE metric_key IN ('active_listings','median_dom','pending_sales',
                                     'pct_price_reductions','median_list_price',
                                     'median_sale_price')
                  AND value IS NOT NULL
                ORDER BY geoid, metric_key, period_end DESC
                """
            )
            for geoid, mk, v, pe in cur.fetchall():
                latest[geoid][mk] = (v, pe)

        # ---- pull 12-month-ago value for YoY computations ----
        yoy: dict[str, dict[str, float]] = defaultdict(dict)
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH latest_per AS (
                    SELECT geoid, metric_key, MAX(period_end) AS latest
                    FROM metrics
                    WHERE metric_key IN ('active_listings','median_list_price','median_sale_price')
                    GROUP BY geoid, metric_key
                )
                SELECT m.geoid, m.metric_key, m.value
                FROM metrics m
                JOIN latest_per lp ON lp.geoid = m.geoid AND lp.metric_key = m.metric_key
                WHERE m.period_end = (lp.latest - INTERVAL '12 months')::date
                  AND m.value IS NOT NULL
                """
            )
            for geoid, mk, v in cur.fetchall():
                yoy[geoid][mk] = v

        print(f"  loaded latest metrics for {len(latest):,} geographies")
        print(f"  loaded 12-mo-ago values for {len(yoy):,} geographies")

        # ---- compute composites ----
        derived_rows: list[tuple] = []  # (geoid, period_end, key, value, value_str)
        for geoid, m in latest.items():
            active = m.get("active_listings", (None,))[0]
            dom = m.get("median_dom", (None,))[0]
            pending = m.get("pending_sales", (None,))[0]
            reductions = m.get("pct_price_reductions", (None,))[0]
            list_price = m.get("median_list_price", (None,))[0]
            sale_price = m.get("median_sale_price", (None,))[0]

            # Latest period across all our inputs
            periods = [pe for (_, pe) in m.values()]
            if not periods:
                continue
            period_end = max(periods)

            # months_supply proxy
            months_supply = active / pending if active and pending and pending > 0 else None

            # liquidity
            liq: float | None = None
            if months_supply is not None and dom is not None:
                liq = 100 * (
                    0.5 * (1 - _clamp(months_supply / 8.0, 0, 1))
                    + 0.5 * (1 - _clamp(dom / 120.0, 0, 1))
                )
            elif dom is not None:
                liq = 100 * (1 - _clamp(dom / 120.0, 0, 1))

            # distress
            distress = 100 * reductions if reductions is not None else None

            # demand pressure (needs YoY)
            price_yoy: float | None = None
            for k in ("median_sale_price", "median_list_price"):
                cur_v = m.get(k, (None,))[0]
                prev_v = yoy.get(geoid, {}).get(k)
                if cur_v and prev_v and prev_v > 0:
                    price_yoy = cur_v / prev_v - 1
                    break
            active_yoy: float | None = None
            cur_a = m.get("active_listings", (None,))[0]
            prev_a = yoy.get(geoid, {}).get("active_listings")
            if cur_a is not None and prev_a is not None and prev_a > 0:
                active_yoy = cur_a / prev_a - 1
            demand: float | None = None
            if price_yoy is not None and active_yoy is not None:
                demand = 100 * (0.6 * price_yoy + 0.4 * (-active_yoy))
            elif price_yoy is not None:
                demand = 100 * price_yoy

            tier = _tier(liq, distress)

            if liq is not None:
                derived_rows.append((geoid, period_end, "liquidity_score", round(liq, 1), None))
            if demand is not None:
                derived_rows.append((geoid, period_end, "demand_pressure",
                                     round(_clamp(demand, -100, 100), 1), None))
            if distress is not None:
                derived_rows.append((geoid, period_end, "distress_indicator",
                                     round(distress, 1), None))
            if tier is not None:
                derived_rows.append((geoid, period_end, "market_tier", None, tier))

        print(f"  computed {len(derived_rows):,} composite metric rows")

        # ---- upsert ----
        BATCH = 5000
        with conn.cursor() as cur:
            for i in range(0, len(derived_rows), BATCH):
                chunk = derived_rows[i : i + BATCH]
                cur.executemany(
                    """
                    INSERT INTO metrics
                        (geoid, metric_key, period_end, period_kind, value, value_str, source)
                    VALUES (%s, %s, %s, 'month', %s, %s, 'derived')
                    ON CONFLICT (geoid, metric_key, period_end) DO UPDATE SET
                        value = EXCLUDED.value,
                        value_str = EXCLUDED.value_str,
                        source = EXCLUDED.source,
                        ingested_at = now()
                    """,
                    chunk,
                )
                conn.commit()
            cur.execute(
                """
                INSERT INTO ingestion_runs
                    (source, started_at, finished_at, status, rows_in, rows_upserted, params)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                ("derived", started, datetime.now(timezone.utc), "success",
                 len(latest), len(derived_rows),
                 Json({"job": "compute_composites"})),
            )
            conn.commit()

    print(f"\n✓ done in {(datetime.now(timezone.utc) - started).total_seconds():.1f}s")


if __name__ == "__main__":
    main()
