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

CREATE_SCENES = """
CREATE TABLE IF NOT EXISTS scenes (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    scene_number INTEGER NOT NULL,
    title VARCHAR(255),
    description TEXT,
    location VARCHAR(255),
    time_of_day VARCHAR(50),
    mood VARCHAR(100),
    dialogue_script TEXT,
    summary TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
)
"""

CREATE_CHARACTERS = """
CREATE TABLE IF NOT EXISTS characters (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name VARCHAR(255) NOT NULL,
    biography TEXT,
    locked_traits TEXT DEFAULT '[]',
    voice_profile_id VARCHAR(255),
    reference_sheet_url TEXT,
    visual_prompt TEXT,
    embedding BLOB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
)
"""

CREATE_ANCHOR_FACES = """
CREATE TABLE IF NOT EXISTS anchor_faces (
    id TEXT PRIMARY KEY,
    character_id TEXT NOT NULL,
    image_url TEXT NOT NULL,
    view_angle VARCHAR(50),
    is_primary BOOLEAN DEFAULT 0,
    embedding BLOB,
    created_at TIMESTAMP,
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
)
"""

CREATE_SHOTS = """
CREATE TABLE IF NOT EXISTS shots (
    id TEXT PRIMARY KEY,
    scene_id TEXT NOT NULL,
    shot_number INTEGER NOT NULL,
    shot_type VARCHAR(50),
    description TEXT,
    camera_angle VARCHAR(50),
    camera_movement VARCHAR(50),
    pacing VARCHAR(50),
    duration_seconds DECIMAL(5,2),
    raw_prompt TEXT,
    injected_prompt TEXT,
    negative_prompt TEXT,
    ip_adapter_weight DECIMAL(4,3),
    character_ids TEXT,
    anchor_face_vectors TEXT,
    motion_type VARCHAR(50),
    assigned_engine VARCHAR(50),
    prompt_text TEXT,
    dialogue_text TEXT,
    video_path TEXT,
    speaker_character_id TEXT,
    status VARCHAR(50) DEFAULT 'PENDING',
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY(scene_id) REFERENCES scenes(id) ON DELETE CASCADE
)
"""

CREATE_RENDER_JOBS = """
CREATE TABLE IF NOT EXISTS render_jobs (
    id TEXT PRIMARY KEY,
    shot_id TEXT NOT NULL,
    engine_name VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'QUEUED',
    output_url TEXT,
    qa_score DECIMAL(4,3),
    qa_feedback TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY(shot_id) REFERENCES shots(id) ON DELETE CASCADE
)
"""

CREATE_SHOOTS = """
CREATE TABLE IF NOT EXISTS shoots (
    id TEXT PRIMARY KEY,
    shot_id TEXT NOT NULL,
    shoot_number INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING',
    engine VARCHAR(50),
    seed INTEGER,
    generation_params TEXT,
    video_path VARCHAR(500),
    audio_path VARCHAR(500),
    thumbnail_path VARCHAR(500),
    clip_score DECIMAL(5,3),
    qwen_diagnosis TEXT,
    qa_status VARCHAR(50),
    qa_timestamp TIMESTAMP,
    duration_seconds DECIMAL(5,2),
    resolution VARCHAR(20),
    fps INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY(shot_id) REFERENCES shots(id) ON DELETE CASCADE
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
        await conn.execute(text(CREATE_SCENES))
        await conn.execute(text(CREATE_CHARACTERS))
        await conn.execute(text(CREATE_ANCHOR_FACES))
        await conn.execute(text(CREATE_SHOTS))
        await conn.execute(text(CREATE_RENDER_JOBS))
        await conn.execute(text(CREATE_SHOOTS))
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
