from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from meridian.config import get_settings

_settings = get_settings()
_engine = create_async_engine(_settings.database_url, pool_pre_ping=True, future=True)
sessionmaker_async = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with sessionmaker_async() as session:
        yield session
