from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from meridian.db.session import get_session
from meridian.services.snapshots import build_snapshot

router = APIRouter()


@router.get("/{geoid}")
async def snapshot(geoid: str, session: AsyncSession = Depends(get_session)) -> dict:
    try:
        snap = await build_snapshot(session, geoid)
    except Exception as e:
        # DB unreachable / query failed — return 404 so frontend shows the
        # "no snapshot for this geo yet" empty state cleanly instead of an
        # "API error" message. The /health endpoint reports the real DB state.
        raise HTTPException(
            status_code=404,
            detail=f"Snapshot for {geoid} unavailable (DB error: {str(e)[:120]})",
        ) from None
    if not snap:
        raise HTTPException(
            status_code=404,
            detail=f"No snapshot data for {geoid}.",
        )
    return snap
