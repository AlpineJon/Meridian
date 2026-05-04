"""Canonical geography dimension tables.

GEOID conventions follow Census FIPS:
  - state:  2-digit state FIPS                        (e.g. "22" Louisiana)
  - county: 5-digit state+county FIPS                 (e.g. "22033" East Baton Rouge)
  - msa:    5-digit CBSA code                         (e.g. "12940" Baton Rouge MSA)
  - place:  7-digit state+place FIPS                  (e.g. "2205000" Baton Rouge city)
  - zip:    5-digit ZCTA                              (e.g. "70809")

ZCTA-to-county/MSA rollups go through ZctaCountyXref. CBSA-to-county delineation
goes through CbsaCountyXref. These are the canonical join surfaces.
"""

from __future__ import annotations

import enum
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from meridian.db.base import Base


class GeoLevel(str, enum.Enum):
    state = "state"
    county = "county"
    msa = "msa"
    place = "place"
    zip = "zip"


class Geography(Base):
    __tablename__ = "geographies"

    geoid: Mapped[str] = mapped_column(String(16), primary_key=True)
    level: Mapped[GeoLevel] = mapped_column(Enum(GeoLevel, name="geo_level"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    state_code: Mapped[str | None] = mapped_column(String(2), index=True)
    parent_geoid: Mapped[str | None] = mapped_column(String(16), ForeignKey("geographies.geoid"), index=True)
    population: Mapped[int | None] = mapped_column(Integer)
    centroid_lon: Mapped[float | None] = mapped_column(Float)
    centroid_lat: Mapped[float | None] = mapped_column(Float)
    # PostGIS geometry — populated from TIGER shapefiles for state/county/msa/place/zip
    geom = mapped_column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    parent: Mapped["Geography | None"] = relationship(
        "Geography", remote_side="Geography.geoid", backref="children"
    )

    __table_args__ = (
        Index("ix_geographies_level_state", "level", "state_code"),
        Index("ix_geographies_geom", "geom", postgresql_using="gist"),
    )


class ZctaCountyXref(Base):
    """ZCTA ↔ County crosswalk (HUD USPS / Census). One ZCTA may span multiple counties."""

    __tablename__ = "zcta_county_xref"

    zcta: Mapped[str] = mapped_column(String(5), primary_key=True)
    county_geoid: Mapped[str] = mapped_column(String(5), primary_key=True)
    res_ratio: Mapped[float] = mapped_column(Float, default=1.0)  # share of residential addresses
    bus_ratio: Mapped[float] = mapped_column(Float, default=1.0)
    src_quarter: Mapped[str] = mapped_column(String(7))  # e.g. "2026Q1"


class CbsaCountyXref(Base):
    """CBSA ↔ County delineation (Census)."""

    __tablename__ = "cbsa_county_xref"

    cbsa_geoid: Mapped[str] = mapped_column(String(5), primary_key=True)
    county_geoid: Mapped[str] = mapped_column(String(5), primary_key=True)
    is_principal: Mapped[bool] = mapped_column(default=False)
    src_year: Mapped[int] = mapped_column(Integer)  # delineation vintage
