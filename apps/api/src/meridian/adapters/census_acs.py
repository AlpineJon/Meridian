"""Census ACS 5-year adapter.

Fetches demographic and housing variables from the U.S. Census Bureau's
American Community Survey 5-year tables for State, MSA (CBSA), Place, and
ZCTA geographies. Maps Census variable codes to our canonical metric_keys.

Reference: https://api.census.gov/data/{year}/acs/acs5/variables.html
"""

from __future__ import annotations

from datetime import date

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from meridian.adapters.base import BaseAdapter, FetchedRow
from meridian.config import get_settings
from meridian.models.metric import SourceName
from meridian.services import cache

# Most recent ACS 5-year release we target
DEFAULT_YEAR = 2023

# Census variable -> our metric_key. None means "internal/intermediate" (used
# to compute a derived metric below; not emitted directly).
VARIABLES: dict[str, str | None] = {
    "B01003_001E": "population",
    "B11001_001E": "households",
    "B19013_001E": "median_household_income",
    "B25003_001E": None,  # _total_occupied_units (denominator for owner/renter pct)
    "B25003_002E": None,  # _owner_occupied_units
    "B25003_003E": None,  # _renter_occupied_units
    "B25077_001E": "median_home_value",
    "B25064_001E": "median_gross_rent",
}


class CensusACSAdapter(BaseAdapter):
    source = SourceName.census_acs
    BASE_URL = "https://api.census.gov/data"

    def __init__(self) -> None:
        self.settings = get_settings()
        self.api_key = self.settings.census_api_key

    # ---- public ----

    async def fetch(
        self,
        *,
        msa_geoids: list[str] | None = None,
        state_geoids: list[str] | None = None,
        place_specs: list[tuple[str, str]] | None = None,  # (state_fips, place_fips)
        zcta_geoids: list[str] | None = None,
        year: int = DEFAULT_YEAR,
    ) -> list[FetchedRow]:
        rows: list[FetchedRow] = []
        if msa_geoids:
            for g in msa_geoids:
                rows.extend(await self._fetch_msa(g, year))
        if state_geoids:
            for g in state_geoids:
                rows.extend(await self._fetch_state(g, year))
        if place_specs:
            for state_fips, place_fips in place_specs:
                place_geoid = state_fips + place_fips
                rows.extend(await self._fetch_place(place_geoid, state_fips, place_fips, year))
        if zcta_geoids:
            for z in zcta_geoids:
                rows.extend(await self._fetch_zcta(z, year))
        return rows

    # ---- internals: per-level fetchers ----

    async def _fetch_msa(self, msa_geoid: str, year: int) -> list[FetchedRow]:
        params = {
            "get": ",".join(VARIABLES.keys()),
            "for": f"metropolitan statistical area/micropolitan statistical area:{msa_geoid}",
        }
        result = await self._cached_get(year, f"msa:{msa_geoid}", params)
        return self._normalize(msa_geoid, result, year)

    async def _fetch_state(self, state_geoid: str, year: int) -> list[FetchedRow]:
        params = {
            "get": ",".join(VARIABLES.keys()),
            "for": f"state:{state_geoid}",
        }
        result = await self._cached_get(year, f"state:{state_geoid}", params)
        return self._normalize(state_geoid, result, year)

    async def _fetch_place(
        self, place_geoid: str, state_fips: str, place_fips: str, year: int
    ) -> list[FetchedRow]:
        params = {
            "get": ",".join(VARIABLES.keys()),
            "for": f"place:{place_fips}",
            "in": f"state:{state_fips}",
        }
        result = await self._cached_get(year, f"place:{place_geoid}", params)
        return self._normalize(place_geoid, result, year)

    async def _fetch_zcta(self, zcta: str, year: int) -> list[FetchedRow]:
        params = {
            "get": ",".join(VARIABLES.keys()),
            "for": f"zip code tabulation area:{zcta}",
        }
        result = await self._cached_get(year, f"zcta:{zcta}", params)
        return self._normalize(zcta, result, year)

    # ---- HTTP w/ cache + retry ----

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def _cached_get(self, year: int, geo_key: str, params: dict) -> dict:
        cache_key = f"meridian:census_acs:{year}:{geo_key}"
        hit = await cache.get_json(cache_key)
        if hit is not None:
            return hit

        url = f"{self.BASE_URL}/{year}/acs/acs5"
        q = dict(params)
        if self.api_key:
            q["key"] = self.api_key

        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(url, params=q)
            r.raise_for_status()
            data = r.json()  # [[headers...], [row1...], ...]

        if not isinstance(data, list) or len(data) < 2:
            raise ValueError(f"Census ACS unexpected response for {geo_key}: {data!r}")
        headers, *rows = data
        if not rows:
            raise ValueError(f"Census ACS returned no data rows for {geo_key}")
        result = dict(zip(headers, rows[0], strict=False))
        await cache.set_json(cache_key, result, ttl=self.settings.cache_ttl_census)
        return result

    # ---- normalize raw census row to FetchedRow records ----

    def _normalize(self, geoid: str, raw: dict, year: int) -> list[FetchedRow]:
        period_end = date(year, 12, 31)
        out: list[FetchedRow] = []

        for census_var, metric_key in VARIABLES.items():
            if metric_key is None:
                continue
            v = raw.get(census_var)
            if v is None or v == "" or v == "-666666666":  # Census null sentinel
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            out.append(
                FetchedRow(
                    geoid=geoid,
                    metric_key=metric_key,
                    period_end=period_end,
                    period_kind="year",
                    value=fv,
                )
            )

        # Derived: owner_occupied_pct, renter_occupied_pct
        total = _safe_float(raw.get("B25003_001E"))
        owner = _safe_float(raw.get("B25003_002E"))
        renter = _safe_float(raw.get("B25003_003E"))
        if total and total > 0:
            out.append(FetchedRow(geoid=geoid, metric_key="owner_occupied_pct",
                                  period_end=period_end, period_kind="year",
                                  value=(owner or 0) / total))
            out.append(FetchedRow(geoid=geoid, metric_key="renter_occupied_pct",
                                  period_end=period_end, period_kind="year",
                                  value=(renter or 0) / total))

        # Derived: rent_to_income (annualized rent / median household income)
        income = _safe_float(raw.get("B19013_001E"))
        rent = _safe_float(raw.get("B25064_001E"))
        if income and income > 0 and rent and rent > 0:
            out.append(FetchedRow(geoid=geoid, metric_key="rent_to_income",
                                  period_end=period_end, period_kind="year",
                                  value=(rent * 12) / income))

        return out


def _safe_float(v) -> float | None:
    if v is None or v == "" or v == "-666666666":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
