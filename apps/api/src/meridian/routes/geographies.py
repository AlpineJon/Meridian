import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from meridian.db.session import get_session
from meridian.services.snapshots import get_geo, list_geographies

router = APIRouter()

# Local fallback used when the database is unreachable. Generated from the
# Census API + us-atlas TopoJSON; doesn't change between database states.
_FALLBACK = Path(__file__).resolve().parent.parent / "data" / "geographies_fallback.json"


def _serve_fallback() -> dict:
    if not _FALLBACK.exists():
        raise HTTPException(status_code=503, detail="DB down and no fallback available")
    return json.loads(_FALLBACK.read_text())


@router.get("")
async def list_all(session: AsyncSession = Depends(get_session)) -> dict:
    try:
        geos = await list_geographies(session)
        if not geos:
            return _serve_fallback()
        return {"geographies": geos}
    except Exception:
        return _serve_fallback()


@router.get("/{geoid}")
async def get_one(geoid: str, session: AsyncSession = Depends(get_session)) -> dict:
    try:
        geo = await get_geo(session, geoid)
        if geo:
            return geo
    except Exception:
        pass
    # fallback lookup
    fb = _serve_fallback()
    for g in fb.get("geographies", []):
        if g["geoid"] == geoid:
            return g
    raise HTTPException(status_code=404, detail=f"Geography {geoid} not found")
