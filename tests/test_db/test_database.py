from sqlalchemy import text

from app.db.database import engine


async def test_engine_creation():
    assert engine is not None


async def test_database_connection():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
