from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from meridian import __version__
from meridian.db.session import get_session

router = APIRouter()


@router.get("/health")
async def health(session: AsyncSession = Depends(get_session)) -> dict:
    db_ok = False
    db_err: str | None = None
    try:
        await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:  # noqa: BLE001
        db_err = str(e)[:200]

    return {
        "ok": db_ok,
        "version": __version__,
        "now": datetime.now(timezone.utc).isoformat(),
        "db": {"ok": db_ok, "error": db_err},
    }
