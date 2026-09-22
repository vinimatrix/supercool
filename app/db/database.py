from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import String

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_uuid_type():
    """Return appropriate UUID type for current database backend."""
    if settings.database_url.startswith("postgresql"):
        from sqlalchemy.dialects.postgresql import UUID as PG_UUID
        return PG_UUID(as_uuid=True)
    return String(36)


def get_json_type():
    """Return appropriate JSON type for current database backend."""
    if settings.database_url.startswith("postgresql"):
        from sqlalchemy.dialects.postgresql import JSONB
        return JSONB
    from sqlalchemy import JSON
    return JSON


async def get_db():
    async with async_session() as session:
        yield session
