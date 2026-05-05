"""Zillow Research adapter — ZHVI (Zillow Home Value Index) at ZIP level.

Source: https://www.zillow.com/research/data/

ZHVI is Zillow's smoothed, seasonally adjusted estimate of "typical home value"
for a given region. It's the best free, monthly, ZIP-level home-value series
in the public data ecosystem.

The CSV is wide-format (one row per region, one column per month). We
transform to our long-format `metrics` schema.
"""

from __future__ import annotations

import csv
import io
import re
from datetime import date

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from meridian.adapters.base import BaseAdapter, FetchedRow
from meridian.models.metric import SourceName


ZHVI_ZIP_URL = (
    "https://files.zillowstatic.com/research/public_csvs/zhvi/"
    "Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
)
ZHVI_METRO_URL = (
    "https://files.zillowstatic.com/research/public_csvs/zhvi/"
    "Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
)
ZORI_ZIP_URL = (
    "https://files.zillowstatic.com/research/public_csvs/zori/"
    "Zip_zori_uc_sfrcondomfr_sm_month.csv"
)


class ZillowAdapter(BaseAdapter):
    source = SourceName.zillow

    HISTORY_MONTHS = 24
    DATE_COL_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    async def fetch(
        self, *, zip_zhvi: bool = True, zip_zori: bool = True
    ) -> list[FetchedRow]:
        rows: list[FetchedRow] = []
        if zip_zhvi:
            rows.extend(
                await self._fetch_wide(
                    ZHVI_ZIP_URL,
                    geo_col="RegionName",
                    pad_to=5,
                    metric_key="median_home_value",
                )
            )
        if zip_zori:
            rows.extend(
                await self._fetch_wide(
                    ZORI_ZIP_URL,
                    geo_col="RegionName",
                    pad_to=5,
                    metric_key="median_gross_rent",
                )
            )
        return rows

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def _fetch_wide(
        self, url: str, *, geo_col: str, pad_to: int, metric_key: str
    ) -> list[FetchedRow]:
        async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
            r = await client.get(url)
            r.raise_for_status()
            text = r.text
        return list(self._parse(text, geo_col=geo_col, pad_to=pad_to, metric_key=metric_key))

    def _parse(self, text: str, *, geo_col: str, pad_to: int, metric_key: str):
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            return
        # Find date columns and trim to most recent N months
        date_cols = sorted(k for k in rows[0].keys() if self.DATE_COL_RE.match(k))
        date_cols = date_cols[-self.HISTORY_MONTHS :]
        if not date_cols:
            return

        for row in rows:
            raw_geo = (row.get(geo_col) or "").strip()
            if not raw_geo or not raw_geo.isdigit():
                continue
            geoid = raw_geo.zfill(pad_to)
            for date_str in date_cols:
                raw = (row.get(date_str) or "").strip()
                if raw in ("", "null", "NA"):
                    continue
                try:
                    val = float(raw)
                except ValueError:
                    continue
                yield FetchedRow(
                    geoid=geoid,
                    metric_key=metric_key,
                    period_end=date.fromisoformat(date_str),
                    period_kind="month",
                    value=val,
                )
