from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from meridian.db.session import get_session
from meridian.services.snapshots import list_summaries

router = APIRouter()


@router.get("")
async def all_summaries(session: AsyncSession = Depends(get_session)) -> dict:
    return {"summaries": await list_summaries(session)}
