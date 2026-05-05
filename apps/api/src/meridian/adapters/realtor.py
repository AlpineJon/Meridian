"""Realtor.com Economic Research adapter.

Pulls the monthly inventory snapshot CSVs that Realtor.com publishes for
free on a stable S3 URL — county-level and metro-level. No auth.

Source: https://www.realtor.com/research/data/

These are the supply + listing-side pricing metrics that Census doesn't give
us: active listings, days on market, new listings, price reductions,
pending sales, $/sqft.

Closed-sale prices and sale-to-list ratios aren't in Realtor.com's public
inventory data — those come from Zillow.
"""

from __future__ import annotations

import csv
import io
from datetime import date
from typing import Iterable

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from meridian.adapters.base import BaseAdapter, FetchedRow
from meridian.models.metric import SourceName

# Realtor.com -> our metric_keys.
# Each tuple: (csv column, our metric_key, transform)
_FLOAT = lambda v: float(v) if v not in ("", None) else None  # noqa: E731

COUNTY_URL = "https://econdata.s3.amazonaws.com/Reports/Core/RDC_Inventory_Core_Metrics_County_History.csv"
METRO_URL = "https://econdata.s3.amazonaws.com/Reports/Core/RDC_Inventory_Core_Metrics_Metro_History.csv"

# (csv_col, metric_key)
COLUMN_MAP: list[tuple[str, str]] = [
    ("median_listing_price", "median_list_price"),
    ("active_listing_count", "active_listings"),
    ("median_days_on_market", "median_dom"),
    ("new_listing_count", "new_listings_monthly"),
    ("price_reduced_share", "pct_price_reductions"),  # already a 0..1 fraction
    ("pending_listing_count", "pending_sales"),
    ("median_listing_price_per_square_foot", "price_per_sqft_list"),
]


class RealtorAdapter(BaseAdapter):
    source = SourceName.realtor

    async def fetch(
        self, *, levels: Iterable[str] = ("county", "metro")
    ) -> list[FetchedRow]:
        rows: list[FetchedRow] = []
        if "county" in levels:
            rows.extend(await self._fetch_csv(COUNTY_URL, geo_col="county_fips", pad_to=5))
        if "metro" in levels:
            rows.extend(await self._fetch_csv(METRO_URL, geo_col="cbsa_code", pad_to=5))
        return rows

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def _fetch_csv(self, url: str, *, geo_col: str, pad_to: int) -> list[FetchedRow]:
        async with httpx.AsyncClient(timeout=180.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            text = r.text
        return list(self._parse(text, geo_col=geo_col, pad_to=pad_to))

    # Keep only the most recent N months of historical data — saves a few
    # million metric rows we don't need for current signals + trailing-12 trend.
    HISTORY_MONTHS = 24

    def _parse(self, text: str, *, geo_col: str, pad_to: int):
        reader = csv.DictReader(io.StringIO(text))
        # First pass: find the max yyyymm so we can filter to a window
        # without loading whole file into memory twice. Streaming approach:
        # parse and collect, then filter at end.
        from datetime import timedelta
        rows_buffered: list = list(reader)
        all_yyyymm = sorted({(r.get("month_date_yyyymm") or "").strip() for r in rows_buffered if r.get("month_date_yyyymm")})
        if not all_yyyymm:
            return
        # Cutoff = max - HISTORY_MONTHS
        latest = all_yyyymm[-1]
        ly, lm = int(latest[:4]), int(latest[4:])
        cutoff_total_months = ly * 12 + lm - self.HISTORY_MONTHS

        for row in rows_buffered:
            yyyymm = (row.get("month_date_yyyymm") or "").strip()
            if len(yyyymm) != 6:
                continue
            year, month = int(yyyymm[:4]), int(yyyymm[4:])
            if year * 12 + month < cutoff_total_months:
                continue  # older than window
            # End-of-month
            if month == 12:
                period_end = date(year + 1, 1, 1)
            else:
                period_end = date(year, month + 1, 1)
            from datetime import timedelta
            period_end = period_end - timedelta(days=1)

            geoid = (row.get(geo_col) or "").strip().zfill(pad_to)
            if not geoid or geoid == "0" * pad_to:
                continue

            for csv_col, metric_key in COLUMN_MAP:
                raw = (row.get(csv_col) or "").strip()
                if raw in ("", "null", "NA"):
                    continue
                try:
                    val = float(raw)
                except ValueError:
                    continue
                yield FetchedRow(
                    geoid=geoid,
                    metric_key=metric_key,
                    period_end=period_end,
                    period_kind="month",
                    value=val,
                )
