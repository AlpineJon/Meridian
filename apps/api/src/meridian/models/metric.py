"""Metric facts and metadata.

Star schema:
  - geographies (dim)
  - metric_definitions (dim) — metric_key, label, source, formula, refresh cadence
  - metrics (fact) — one row per (geo, metric_key, period_end)
  - ingestion_runs (audit) — one row per adapter run
"""

from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from meridian.db.base import Base


class SourceName(str, enum.Enum):
    census_acs = "census_acs"
    census_bps = "census_bps"
    bls_laus = "bls_laus"
    fred = "fred"
    realtor = "realtor"
    zillow = "zillow"
    derived = "derived"  # composite signals
    seed = "seed"


class MetricDefinition(Base):
    """Glossary row per metric_key. Single source of truth for the front end."""

    __tablename__ = "metric_definitions"

    metric_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(32), index=True)  # supply | pricing | demo | composite
    unit: Mapped[str] = mapped_column(String(16))  # usd | pct | count | days | months | score | tier
    source: Mapped[SourceName] = mapped_column(Enum(SourceName, name="source_name"))
    refresh_cadence: Mapped[str] = mapped_column(String(32))  # daily | weekly | monthly | annual
    description: Mapped[str] = mapped_column(String(1024))
    formula: Mapped[str | None] = mapped_column(String(2048))  # null for raw metrics


class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    geoid: Mapped[str] = mapped_column(String(16), ForeignKey("geographies.geoid"), index=True)
    metric_key: Mapped[str] = mapped_column(
        String(64), ForeignKey("metric_definitions.metric_key"), index=True
    )
    period_end: Mapped[date] = mapped_column(Date, index=True)  # last day of the period the value covers
    period_kind: Mapped[str] = mapped_column(String(16))  # day | week | month | quarter | year
    value: Mapped[float | None] = mapped_column(Float)
    value_str: Mapped[str | None] = mapped_column(String(64))  # for categorical (e.g., tier "A")
    source: Mapped[SourceName] = mapped_column(Enum(SourceName, name="source_name"))
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("geoid", "metric_key", "period_end", name="uq_metric_value"),
        Index("ix_metrics_geo_key_period", "geoid", "metric_key", "period_end"),
    )


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[SourceName] = mapped_column(Enum(SourceName, name="source_name"))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16))  # running | success | failed
    rows_in: Mapped[int] = mapped_column(Integer, default=0)
    rows_upserted: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(String(2048))
    params: Mapped[dict | None] = mapped_column(JSON)  # adapter-specific params (e.g. acs_year, geos)
