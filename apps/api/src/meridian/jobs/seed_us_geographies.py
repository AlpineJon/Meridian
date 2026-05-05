"""Bulk-load US-wide geographies into Postgres.

Inserts:
  - 52 states (50 + DC + PR) — hardcoded list with FIPS + abbr
  - All MSAs (~939 metropolitan + micropolitan) — fetched from Census API
  - All US counties (~3,200) — fetched from us-atlas TopoJSON CDN

Idempotent (uses ON CONFLICT). Run with:
    uv run python -m meridian.jobs.seed_us_geographies
"""

from __future__ import annotations

import asyncio
import re
from typing import Any

import httpx
import psycopg
import us

from meridian.config import get_settings


# ---- 52 states (50 + DC + PR) ----
# Hardcoded subset of `us.states.STATES_AND_TERRITORIES` filtered to
# what we want in the rail.
STATE_NAMES_INCLUDED = {s.fips: (s.abbr, s.name) for s in us.states.STATES + [us.states.DC, us.states.PR]}


# Approximate state centroids (lon, lat) — for fly-to in the map
STATE_CENTROIDS: dict[str, tuple[float, float]] = {
    "01": (-86.79, 32.81), "02": (-152.40, 64.20), "04": (-111.66, 34.17), "05": (-92.44, 34.90),
    "06": (-119.42, 36.78), "08": (-105.55, 38.99), "09": (-72.76, 41.62), "10": (-75.51, 38.99),
    "11": (-77.04, 38.91), "12": (-81.69, 27.77), "13": (-83.43, 32.65), "15": (-156.34, 20.30),
    "16": (-114.48, 44.07), "17": (-89.20, 40.05), "18": (-86.13, 39.85), "19": (-93.21, 42.07),
    "20": (-98.32, 38.50), "21": (-84.86, 37.84), "22": (-91.96, 31.00), "23": (-69.38, 45.37),
    "24": (-76.65, 39.05), "25": (-71.81, 42.24), "26": (-84.66, 44.31), "27": (-94.31, 46.28),
    "28": (-89.66, 32.74), "29": (-92.28, 38.36), "30": (-110.44, 47.05), "31": (-99.79, 41.50),
    "32": (-117.05, 38.50), "33": (-71.58, 43.45), "34": (-74.52, 40.30), "35": (-106.25, 34.84),
    "36": (-75.00, 42.95), "37": (-79.81, 35.63), "38": (-100.47, 47.53), "39": (-82.79, 40.39),
    "40": (-97.50, 35.57), "41": (-122.07, 44.57), "42": (-77.21, 40.59), "44": (-71.52, 41.68),
    "45": (-80.95, 33.86), "46": (-99.44, 44.30), "47": (-86.69, 35.86), "48": (-97.56, 31.05),
    "49": (-111.86, 40.15), "50": (-72.71, 44.04), "51": (-78.17, 37.77), "53": (-121.49, 47.40),
    "54": (-80.95, 38.49), "55": (-89.62, 44.27), "56": (-107.30, 42.75), "72": (-66.59, 18.20),
}


def _sync_url() -> str:
    return get_settings().database_url_sync.replace("postgresql+psycopg://", "postgresql://", 1)


# ---- helpers ----

def _state_abbr_from_msa_name(name: str) -> str | None:
    """Extract first state abbr from 'Baton Rouge, LA Metro Area' -> 'LA'."""
    # Split on comma; second part starts with abbr or abbr-abbr-abbr
    if "," not in name:
        return None
    after = name.split(",", 1)[1].strip()
    m = re.match(r"([A-Z]{2})(?:[- ]|$)", after)
    return m.group(1) if m else None


def _clean_msa_name(raw: str) -> str:
    """'Baton Rouge, LA Metro Area' -> 'Baton Rouge, LA'."""
    return re.sub(r"\s+(Metro|Micro)\s+Area$", "", raw, flags=re.IGNORECASE)


# ---- fetchers ----

async def fetch_msas_from_census() -> list[dict[str, Any]]:
    """Pull all CBSAs (metro + micro) with name + population from Census ACS."""
    url = "https://api.census.gov/data/2023/acs/acs5"
    params: dict[str, str] = {
        "get": "NAME,B01003_001E",
        "for": "metropolitan statistical area/micropolitan statistical area:*",
    }
    api_key = get_settings().census_api_key
    if api_key:
        params["key"] = api_key

    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()

    headers, *rows = data
    name_idx = headers.index("NAME")
    pop_idx = headers.index("B01003_001E")
    geo_idx = headers.index("metropolitan statistical area/micropolitan statistical area")

    msas: list[dict[str, Any]] = []
    for row in rows:
        raw_name = row[name_idx]
        cbsa = row[geo_idx]
        try:
            pop = int(row[pop_idx]) if row[pop_idx] not in (None, "", "-666666666") else None
        except (TypeError, ValueError):
            pop = None
        state_abbr = _state_abbr_from_msa_name(raw_name)
        state_obj = us.states.lookup(state_abbr) if state_abbr else None
        msas.append({
            "geoid": cbsa,
            "level": "msa",
            "name": _clean_msa_name(raw_name),
            "state_code": state_abbr,
            "parent_geoid": state_obj.fips if state_obj else None,
            "population": pop,
            "centroid_lon": None,
            "centroid_lat": None,
        })
    return msas


async def fetch_counties_from_atlas() -> list[dict[str, Any]]:
    """Load county FIPS + name + parent state from us-atlas TopoJSON CDN."""
    url = "https://cdn.jsdelivr.net/npm/us-atlas@3/counties-10m.json"
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        topo = r.json()

    # us-atlas TopoJSON: objects.counties.geometries[i].id is the 5-digit FIPS,
    # geometries[i].properties.name is the county name.
    geoms = topo["objects"]["counties"]["geometries"]
    counties: list[dict[str, Any]] = []
    valid_state_fips = set(STATE_NAMES_INCLUDED.keys())
    for g in geoms:
        fips5 = str(g.get("id", "")).zfill(5)
        if len(fips5) != 5:
            continue
        state_fips = fips5[:2]
        if state_fips not in valid_state_fips:
            continue  # skip territories not in our state set (AS/GU/MP/VI)
        name = g.get("properties", {}).get("name", "")
        state_obj = us.states.lookup(state_fips)
        counties.append({
            "geoid": fips5,
            "level": "county",
            "name": name,
            "state_code": state_obj.abbr if state_obj else None,
            "parent_geoid": state_fips,
            "population": None,
            "centroid_lon": None,
            "centroid_lat": None,
        })
    return counties


def upsert_geographies(conn: psycopg.Connection, rows: list[dict[str, Any]]) -> int:
    sql = """
        INSERT INTO geographies (geoid, level, name, state_code, parent_geoid,
                                 population, centroid_lon, centroid_lat)
        VALUES (%(geoid)s, %(level)s, %(name)s, %(state_code)s, %(parent_geoid)s,
                %(population)s, %(centroid_lon)s, %(centroid_lat)s)
        ON CONFLICT (geoid) DO UPDATE SET
            level = EXCLUDED.level,
            name = EXCLUDED.name,
            state_code = EXCLUDED.state_code,
            parent_geoid = COALESCE(geographies.parent_geoid, EXCLUDED.parent_geoid),
            population = COALESCE(EXCLUDED.population, geographies.population),
            centroid_lon = COALESCE(EXCLUDED.centroid_lon, geographies.centroid_lon),
            centroid_lat = COALESCE(EXCLUDED.centroid_lat, geographies.centroid_lat),
            updated_at = now()
    """
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    return len(rows)


# ---- main ----

async def run() -> None:
    print("Loading US-wide geographies into Supabase…")

    # 1) States
    states_rows = []
    for fips, (abbr, name) in sorted(STATE_NAMES_INCLUDED.items()):
        c = STATE_CENTROIDS.get(fips, (None, None))
        states_rows.append({
            "geoid": fips, "level": "state", "name": name,
            "state_code": abbr, "parent_geoid": None,
            "population": None,
            "centroid_lon": c[0], "centroid_lat": c[1],
        })

    # 2) MSAs from Census
    print("  fetching MSAs from Census API…")
    msas_rows = await fetch_msas_from_census()
    print(f"    got {len(msas_rows)} MSAs")

    # 3) Counties from us-atlas
    print("  fetching counties from us-atlas TopoJSON…")
    counties_rows = await fetch_counties_from_atlas()
    print(f"    got {len(counties_rows)} counties")

    # 4) Upsert
    print("  upserting…")
    with psycopg.connect(_sync_url()) as conn:
        # States must exist first because MSAs/counties FK to them via parent_geoid.
        n1 = upsert_geographies(conn, states_rows)
        print(f"    ✓ states: {n1}")
        n2 = upsert_geographies(conn, msas_rows)
        print(f"    ✓ MSAs:   {n2}")
        n3 = upsert_geographies(conn, counties_rows)
        print(f"    ✓ counties: {n3}")
        conn.commit()
    print(f"\nTotal: {n1 + n2 + n3} geographies in Supabase.")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
