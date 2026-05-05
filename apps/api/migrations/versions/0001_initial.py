"""initial schema — geographies, metrics, ingestion runs

Revision ID: 0001
Revises:
Create Date: 2026-05-04
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE geo_level AS ENUM ('state','county','msa','place','zip');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE source_name AS ENUM (
                'census_acs','census_bps','bls_laus','fred','realtor','zillow','derived','seed'
            );
        EXCEPTION WHEN duplicate_object THEN null; END $$;
        """
    )

    # ---- geographies ----
    op.execute(
        """
        CREATE TABLE geographies (
            geoid           VARCHAR(16) PRIMARY KEY,
            level           geo_level NOT NULL,
            name            VARCHAR(255) NOT NULL,
            state_code      VARCHAR(2),
            parent_geoid    VARCHAR(16) REFERENCES geographies(geoid),
            population      INTEGER,
            centroid_lon    DOUBLE PRECISION,
            centroid_lat    DOUBLE PRECISION,
            geom            geometry(MultiPolygon, 4326),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_geographies_level ON geographies (level)")
    op.execute("CREATE INDEX ix_geographies_state_code ON geographies (state_code)")
    op.execute("CREATE INDEX ix_geographies_parent_geoid ON geographies (parent_geoid)")
    op.execute("CREATE INDEX ix_geographies_level_state ON geographies (level, state_code)")
    op.execute("CREATE INDEX ix_geographies_geom ON geographies USING gist (geom)")

    # ---- zcta_county_xref ----
    op.execute(
        """
        CREATE TABLE zcta_county_xref (
            zcta            VARCHAR(5) NOT NULL,
            county_geoid    VARCHAR(5) NOT NULL,
            res_ratio       DOUBLE PRECISION DEFAULT 1.0,
            bus_ratio       DOUBLE PRECISION DEFAULT 1.0,
            src_quarter     VARCHAR(7) NOT NULL,
            PRIMARY KEY (zcta, county_geoid)
        )
        """
    )

    # ---- cbsa_county_xref ----
    op.execute(
        """
        CREATE TABLE cbsa_county_xref (
            cbsa_geoid      VARCHAR(5) NOT NULL,
            county_geoid    VARCHAR(5) NOT NULL,
            is_principal    BOOLEAN DEFAULT FALSE,
            src_year        INTEGER NOT NULL,
            PRIMARY KEY (cbsa_geoid, county_geoid)
        )
        """
    )

    # ---- metric_definitions ----
    op.execute(
        """
        CREATE TABLE metric_definitions (
            metric_key      VARCHAR(64) PRIMARY KEY,
            label           VARCHAR(128) NOT NULL,
            category        VARCHAR(32) NOT NULL,
            unit            VARCHAR(16) NOT NULL,
            source          source_name NOT NULL,
            refresh_cadence VARCHAR(32) NOT NULL,
            description     VARCHAR(1024) NOT NULL,
            formula         VARCHAR(2048)
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_metric_definitions_category ON metric_definitions (category)"
    )

    # ---- metrics ----
    op.execute(
        """
        CREATE TABLE metrics (
            id              SERIAL PRIMARY KEY,
            geoid           VARCHAR(16) NOT NULL REFERENCES geographies(geoid),
            metric_key      VARCHAR(64) NOT NULL REFERENCES metric_definitions(metric_key),
            period_end      DATE NOT NULL,
            period_kind     VARCHAR(16) NOT NULL,
            value           DOUBLE PRECISION,
            value_str       VARCHAR(64),
            source          source_name NOT NULL,
            ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_metric_value UNIQUE (geoid, metric_key, period_end)
        )
        """
    )
    op.execute("CREATE INDEX ix_metrics_geoid ON metrics (geoid)")
    op.execute("CREATE INDEX ix_metrics_metric_key ON metrics (metric_key)")
    op.execute("CREATE INDEX ix_metrics_period_end ON metrics (period_end)")
    op.execute(
        "CREATE INDEX ix_metrics_geo_key_period ON metrics (geoid, metric_key, period_end)"
    )

    # ---- ingestion_runs ----
    op.execute(
        """
        CREATE TABLE ingestion_runs (
            id              SERIAL PRIMARY KEY,
            source          source_name NOT NULL,
            started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            finished_at     TIMESTAMPTZ,
            status          VARCHAR(16) NOT NULL,
            rows_in         INTEGER DEFAULT 0,
            rows_upserted   INTEGER DEFAULT 0,
            error           VARCHAR(2048),
            params          JSONB
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ingestion_runs CASCADE")
    op.execute("DROP TABLE IF EXISTS metrics CASCADE")
    op.execute("DROP TABLE IF EXISTS metric_definitions CASCADE")
    op.execute("DROP TABLE IF EXISTS cbsa_county_xref CASCADE")
    op.execute("DROP TABLE IF EXISTS zcta_county_xref CASCADE")
    op.execute("DROP TABLE IF EXISTS geographies CASCADE")
    op.execute("DROP TYPE IF EXISTS source_name CASCADE")
    op.execute("DROP TYPE IF EXISTS geo_level CASCADE")
