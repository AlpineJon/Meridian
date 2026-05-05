"""Build the GeoSnapshot JSON shape consumed by the Next.js frontend.

The shape mirrors apps/web/src/lib/seed.ts.GeoSnapshot exactly so the web
client can swap from the seed data to /snapshots/{geoid} without changing
its types.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Map our metric_keys -> the camelCase keys the frontend expects
SUPPLY_KEYS = {
    "active_listings": "activeListings",
    "new_listings_monthly": "newListingsMonthly",
    "new_listings_yoy": "newListingsYoY",
    "months_supply": "monthsSupply",
    "median_dom": "medianDom",
    "pct_price_reductions": "pctPriceReductions",
    "permits_1unit_12mo": "permits1Unit12mo",
    "permits_2to4_12mo": "permits24Unit12mo",
    "permits_5plus_12mo": "permits5plus12mo",
}
PRICING_KEYS = {
    "median_sale_price": "medianSalePrice",
    "median_list_price": "medianListPrice",
    "sale_to_list_ratio": "saleToListRatio",
    "price_per_sqft_sold": "pricePerSqftSold",
    "price_per_sqft_list": "pricePerSqftList",
    "sale_price_yoy": "salePriceYoY",
    "sale_price_cagr_3y": "salePriceCagr3y",
    "pending_sales": "pendingSales",
    "closed_sales": "closedSales",
}
DEMO_KEYS = {
    "population": "population",
    "households": "households",
    "median_household_income": "medianIncome",
    "owner_occupied_pct": "ownerOccupiedPct",
    "renter_occupied_pct": "renterOccupiedPct",
    "median_home_value": "medianHomeValue",
    "median_gross_rent": "medianGrossRent",
    "rent_to_income": "rentToIncome",
    "pop_growth_5y": "popGrowth5y",
    "unemployment_rate": "unemploymentRate",
}
SIGNAL_KEYS = {
    "liquidity_score": "liquidityScore",
    "demand_pressure": "demandPressure",
    "distress_indicator": "distressIndicator",
    "market_tier": "marketTier",
}

# Trends — which metrics ship with a 12-mo trend block
TREND_METRIC_KEYS = {
    "active_listings": "activeListingsTrend",
    "months_supply": "monthsSupplyTrend",
    "median_dom": "medianDomTrend",
    "permits_1unit_monthly": "permitsTrend",
    "median_sale_price": "salePriceTrend",
}

# Routing: which output group each trend belongs to (supply | pricing | demo)
TREND_TO_GROUP: dict[str, str] = {
    "active_listings": "supply",
    "months_supply": "supply",
    "median_dom": "supply",
    "permits_1unit_monthly": "supply",
    "median_sale_price": "pricing",
}

# Source labels for the freshness footer (per source enum)
SOURCE_LABELS = {
    "census_acs": "Census ACS 5-yr (2019-2023)",
    "realtor": "Realtor.com Economic Research",
    "bls_laus": "BLS LAUS",
    "census_bps": "Census BPS",
    "fred": "FRED",
    "zillow": "Zillow Research",
    "derived": "Derived (composite signals)",
    "seed": "Seed bootstrap",
}


async def get_geo(session: AsyncSession, geoid: str) -> dict | None:
    row = (
        await session.execute(
            text(
                """
                SELECT geoid, level::text, name, state_code, parent_geoid, population
                FROM geographies WHERE geoid = :geoid
                """
            ),
            {"geoid": geoid},
        )
    ).first()
    if not row:
        return None
    return {
        "geoid": row.geoid,
        "level": row.level,
        "name": row.name,
        "state": row.state_code,
        "parent": row.parent_geoid,
        "population": row.population,
    }


async def list_summaries(session: AsyncSession) -> list[dict]:
    """One row per geography with just the four composite signals + name/level.

    Used by MapView for choropleth shading without fetching full snapshots.
    """
    rows = (
        await session.execute(
            text(
                """
                WITH latest AS (
                    SELECT DISTINCT ON (geoid, metric_key)
                           geoid, metric_key, value, value_str, period_end
                    FROM metrics
                    WHERE metric_key IN
                        ('liquidity_score','demand_pressure','distress_indicator','market_tier')
                    ORDER BY geoid, metric_key, period_end DESC
                )
                SELECT g.geoid, g.level::text AS level, g.name, g.state_code, g.parent_geoid,
                       MAX(CASE WHEN l.metric_key='liquidity_score' THEN l.value END) AS liquidity,
                       MAX(CASE WHEN l.metric_key='demand_pressure' THEN l.value END) AS demand,
                       MAX(CASE WHEN l.metric_key='distress_indicator' THEN l.value END) AS distress,
                       MAX(CASE WHEN l.metric_key='market_tier' THEN l.value_str END) AS tier
                FROM geographies g
                LEFT JOIN latest l ON l.geoid = g.geoid
                GROUP BY g.geoid, g.level, g.name, g.state_code, g.parent_geoid
                ORDER BY g.level, g.state_code, g.name
                """
            )
        )
    ).all()
    return [
        {
            "geoid": r.geoid,
            "level": r.level,
            "name": r.name,
            "state": r.state_code,
            "parent": r.parent_geoid,
            "signals": {
                "liquidityScore": int(r.liquidity) if r.liquidity is not None else None,
                "demandPressure": int(r.demand) if r.demand is not None else None,
                "distressIndicator": int(r.distress) if r.distress is not None else None,
                "marketTier": r.tier,
            },
        }
        for r in rows
    ]


async def list_geographies(session: AsyncSession) -> list[dict]:
    rows = (
        await session.execute(
            text(
                """
                SELECT geoid, level::text, name, state_code, parent_geoid, population
                FROM geographies
                ORDER BY level, state_code, name
                """
            )
        )
    ).all()
    return [
        {
            "geoid": r.geoid,
            "level": r.level,
            "name": r.name,
            "state": r.state_code,
            "parent": r.parent_geoid,
            "population": r.population,
        }
        for r in rows
    ]


async def build_snapshot(session: AsyncSession, geoid: str) -> dict | None:
    geo = await get_geo(session, geoid)
    if not geo:
        return None

    # Latest value per metric_key (handles mixed cadences: annual demographics
    # + monthly listings). DISTINCT ON gets the freshest value per key.
    point_rows = (
        await session.execute(
            text(
                """
                SELECT DISTINCT ON (metric_key)
                       metric_key, value, value_str, source::text AS source,
                       period_end, ingested_at
                FROM metrics
                WHERE geoid = :geoid
                ORDER BY metric_key, period_end DESC
                """
            ),
            {"geoid": geoid},
        )
    ).all()

    if not point_rows:
        return None

    points: dict[str, tuple[float | None, str | None, str, str]] = {
        r.metric_key: (r.value, r.value_str, r.source, r.ingested_at.date().isoformat())
        for r in point_rows
    }

    # Trends — last 12 months of monthly values for trend metrics
    trend_rows = (
        await session.execute(
            text(
                """
                SELECT metric_key, to_char(period_end, 'YYYY-MM') AS month, value
                FROM metrics
                WHERE geoid = :geoid
                  AND metric_key = ANY(:keys)
                  AND period_kind = 'month'
                ORDER BY metric_key, period_end
                """
            ),
            {"geoid": geoid, "keys": list(TREND_METRIC_KEYS.keys())},
        )
    ).all()

    trends: dict[str, dict[str, list]] = {}
    for r in trend_rows:
        bucket = trends.setdefault(r.metric_key, {"months": [], "values": []})
        bucket["months"].append(r.month)
        bucket["values"].append(float(r.value) if r.value is not None else None)

    def num(key: str) -> float | None:
        v = points.get(key)
        if not v or v[0] is None:
            return None
        return v[0]

    def text_val(key: str) -> str | None:
        v = points.get(key)
        return v[1] if v else None

    # ---- shape signals ----
    def to_int_or_none(v):
        return int(v) if v is not None else None

    signals = {
        SIGNAL_KEYS["liquidity_score"]: to_int_or_none(num("liquidity_score")),
        SIGNAL_KEYS["demand_pressure"]: to_int_or_none(num("demand_pressure")),
        SIGNAL_KEYS["distress_indicator"]: to_int_or_none(num("distress_indicator")),
        SIGNAL_KEYS["market_tier"]: text_val("market_tier"),
        "rationale": {
            "liquidity": text_val("rationale_liquidity") or "",
            "demand": text_val("rationale_demand") or "",
            "distress": text_val("rationale_distress") or "",
            "tier": text_val("rationale_tier") or "",
        },
    }

    # ---- shape supply / pricing / demo ----
    supply: dict = {camel: num(snake) for snake, camel in SUPPLY_KEYS.items()}
    pricing: dict = {camel: num(snake) for snake, camel in PRICING_KEYS.items()}
    demo: dict = {camel: num(snake) for snake, camel in DEMO_KEYS.items()}

    # Attach trends to the right group via TREND_TO_GROUP
    for snake, trend_camel in TREND_METRIC_KEYS.items():
        if snake not in trends:
            continue
        group = TREND_TO_GROUP.get(snake)
        if group == "supply":
            supply[trend_camel] = trends[snake]
        elif group == "pricing":
            pricing[trend_camel] = trends[snake]
        elif group == "demo":
            demo[trend_camel] = trends[snake]

    # ---- freshness footer ----
    fresh_rows = (
        await session.execute(
            text(
                """
                SELECT m.source::text AS source, MAX(m.ingested_at)::date AS updated
                FROM metrics m
                WHERE m.geoid = :geoid
                GROUP BY m.source
                ORDER BY m.source
                """
            ),
            {"geoid": geoid},
        )
    ).all()
    freshness = [
        {"source": SOURCE_LABELS.get(r.source, r.source), "updatedAt": r.updated.isoformat()}
        for r in fresh_rows
    ]

    return {
        "geo": geo,
        "signals": signals,
        "supply": supply,
        "pricing": pricing,
        "demo": demo,
        "freshness": freshness,
    }
