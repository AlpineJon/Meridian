# Meridian

Market intelligence dashboard for residential real estate credit. Built for ROC360-style
RTL/bridge underwriters who need to size loans, set ARV haircuts, and assess market
liquidity at the state, MSA, city, and ZIP level.

## What it does

- Ingests housing **supply, pricing, demographics, and permits** from public APIs
  (Census ACS, BLS LAUS, FRED, Census BPS, Zillow Research, Realtor.com) on scheduled
  jobs.
- Aggregates ZIP → County/MSA → State using FIPS codes as canonical keys.
- Computes four **credit-relevant composite signals**: Liquidity Score, Demand Pressure,
  Distress Indicator, Market Tier (A/B/C/D).
- Surfaces them in a Next.js dashboard designed for credit-officer workflow density,
  not consumer browsing.

## Architecture

```
meridian/
├── apps/
│   ├── api/        FastAPI + SQLAlchemy + Alembic + Pydantic v2
│   └── web/        Next.js 15 (App Router) + TS + Tailwind + TanStack Query
├── packages/
│   └── shared-types/   TS types generated from FastAPI's OpenAPI schema
├── seed/           CSV seed data for Baton Rouge MSA + 5 comparison MSAs
└── docs/
    └── METRICS.md  Per-metric definitions, sources, refresh cadence, formulas
```

**Stack:** Python 3.12 / FastAPI / SQLAlchemy 2.0 / Pydantic v2 / Alembic /
Postgres 16 + PostGIS / Redis / Prefect (scheduled ingestion) / Next.js 15 /
TypeScript / Tailwind / TanStack Query / Recharts / MapLibre GL.

**Why this stack:** Census/BLS/FRED ecosystems are Python-first, GeoPandas + TIGER
shapefile ingest is painful outside Python, Pydantic↔OpenAPI gives the web client
free typed contracts, MapLibre is open-source and ditches Mapbox tokens.

## Status

| Phase | Scope | Status |
|---|---|---|
| 1 | Repo scaffold, schema, Census ACS adapter, ZIP demographics vertical slice | In progress |
| 2 | Zillow / Realtor / BPS / BLS adapters, composite signals, comparison + trend views | Pending |
| 3 | Choropleth map, export, alerts, saved geographies, auth stub | Pending |

## Getting started

Prerequisites: Python 3.12, Node 20+, Postgres 16 with PostGIS, Redis. See
[docs/SETUP.md](docs/SETUP.md) for install instructions.

```bash
# one-time
./scripts/bootstrap.sh

# run everything
./scripts/dev.sh
```

API runs on `:8000`, web on `:3000`.

## Data sources

See [docs/METRICS.md](docs/METRICS.md) for the full list. All metrics document their
upstream source and refresh cadence. **No mock data in the prototype** beyond the seed
bootstrap — every tile traces to a real source.

## License

Proprietary. Internal prototype.
