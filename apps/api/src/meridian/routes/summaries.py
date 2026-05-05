import json
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from meridian.db.session import get_session
from meridian.services.snapshots import list_summaries

router = APIRouter()

_FALLBACK = Path(__file__).resolve().parent.parent / "data" / "geographies_fallback.json"


def _serve_fallback() -> dict:
    """Return summaries with empty signals when DB is down."""
    if not _FALLBACK.exists():
        return {"summaries": []}
    geos = json.loads(_FALLBACK.read_text()).get("geographies", [])
    return {
        "summaries": [
            {
                **g,
                "signals": {
                    "liquidityScore": None,
                    "demandPressure": None,
                    "distressIndicator": None,
                    "marketTier": None,
                },
            }
            for g in geos
        ]
    }


@router.get("")
async def all_summaries(session: AsyncSession = Depends(get_session)) -> dict:
    try:
        summs = await list_summaries(session)
        if not summs:
            return _serve_fallback()
        return {"summaries": summs}
    except Exception:
        return _serve_fallback()
