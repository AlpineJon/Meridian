from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from meridian.db.session import get_session
from meridian.services.snapshots import build_snapshot

router = APIRouter()


@router.get("/{geoid}")
async def snapshot(geoid: str, session: AsyncSession = Depends(get_session)) -> dict:
    snap = await build_snapshot(session, geoid)
    if not snap:
        raise HTTPException(
            status_code=404,
            detail=f"No snapshot data for {geoid}. Run the seeder or wait for ingestion.",
        )
    return snap
