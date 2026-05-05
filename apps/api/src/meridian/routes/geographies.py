from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from meridian.db.session import get_session
from meridian.services.snapshots import get_geo, list_geographies

router = APIRouter()


@router.get("")
async def list_all(session: AsyncSession = Depends(get_session)) -> dict:
    return {"geographies": await list_geographies(session)}


@router.get("/{geoid}")
async def get_one(geoid: str, session: AsyncSession = Depends(get_session)) -> dict:
    geo = await get_geo(session, geoid)
    if not geo:
        raise HTTPException(status_code=404, detail=f"Geography {geoid} not found")
    return geo
