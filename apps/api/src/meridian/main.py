"""FastAPI entry point for the Meridian backend."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from meridian import __version__
from meridian.routes import geographies as geo_routes
from meridian.routes import health as health_routes
from meridian.routes import snapshots as snap_routes
from meridian.routes import summaries as summ_routes


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Meridian API",
        version=__version__,
        description="Market intelligence backend for residential RE credit underwriting.",
        lifespan=lifespan,
    )

    # Allow the Next.js dev server (and prod web) to call us
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3100",
            "http://127.0.0.1:3100",
        ],
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    app.include_router(health_routes.router)
    app.include_router(geo_routes.router, prefix="/geographies", tags=["geographies"])
    app.include_router(snap_routes.router, prefix="/snapshots", tags=["snapshots"])
    app.include_router(summ_routes.router, prefix="/summaries", tags=["summaries"])

    return app


app = create_app()
