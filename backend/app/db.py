from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import settings


class Base(DeclarativeBase):
    pass


# NullPool: don't cache connections across asyncio event loops.
# Celery creates a fresh loop per task via asyncio.run(), and a pooled
# connection bound to a dead loop crashes asyncpg.
engine = create_async_engine(settings.database_url, poolclass=NullPool, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
