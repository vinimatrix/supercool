import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.main import create_app

CREATE_PROJECTS = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    target_resolution VARCHAR(20) DEFAULT '4K',
    fps INTEGER DEFAULT 24,
    aspect_ratio VARCHAR(10) DEFAULT '16:9',
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
"""


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.execute(text(CREATE_PROJECTS))
    test_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await engine.dispose()
