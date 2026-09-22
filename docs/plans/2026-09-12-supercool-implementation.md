# SuperCool - AI Cinematic Studio: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the SuperCool AI Cinematic Studio MVP — a Python + Rust hybrid system for AI-powered film production with Story Bible, prompt injection, and NLE video processing.

**Architecture:** FastAPI (Python) serves REST API and orchestrates services. Rust Axum server handles FFmpeg NLE operations. PostgreSQL + pgvector stores data and anchor face embeddings. Multi-provider LLM abstraction (Google/OpenAI/NVIDIA).

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0, PostgreSQL, pgvector, Rust, Axum, FFmpeg, Celery, Redis, Docker

## Global Constraints

- Python ≥ 3.12, Rust ≥ 1.75
- PostgreSQL 16 + pgvector extension
- FFmpeg 6.x with NVENC support
- UUID primary keys everywhere (gen_random_uuid())
- All timestamps UTC (TIMESTAMPTZ)
- Type hints on all Python functions
- TDD: write failing test first, then implement
- Frequent commits per task

---

## File Structure

```
supercool/
├── pyproject.toml                    # Python project config (uv)
├── Cargo.toml                        # Rust workspace
├── rust-nle/
│   ├── Cargo.toml
│   └── src/
│       ├── main.rs                   # Axum server entry
│       ├── lib.rs                    # Public API
│       ├── ffmpeg/
│       │   ├── mod.rs
│       │   ├── concat.rs
│       │   ├── transcode.rs
│       │   └── audio.rs
│       └── pipeline.rs
├── app/
│   ├── __init__.py
│   ├── main.py                       # FastAPI app factory
│   ├── config.py                     # Settings
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py               # Engine, session, Base
│   ├── models/
│   │   ├── __init__.py
│   │   ├── project.py
│   │   ├── character.py
│   │   ├── scene.py
│   │   ├── shot.py
│   │   └── render_job.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── project.py
│   │   ├── character.py
│   │   ├── scene.py
│   │   ├── shot.py
│   │   └── render_job.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── projects.py
│   │       ├── scenes.py
│   │       ├── shots.py
│   │       ├── story_bible.py
│   │       └── render.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── story_bible.py
│   │   ├── context_injector.py
│   │   ├── nle_client.py
│   │   └── render_service.py
│   └── providers/
│       ├── __init__.py
│       ├── base.py
│       ├── google.py
│       ├── openai.py
│       ├── nvidia.py
│       └── registry.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_models/
│   ├── test_api/
│   ├── test_services/
│   └── test_providers/
└── alembic/
    └── versions/
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `Cargo.toml`
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `app/config.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Interfaces:**
- Consumes: None (first task)
- Produces: `create_app()` factory, `Settings` class

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "supercool"
version = "0.1.0"
description = "AI Cinematic Studio"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy[asyncio]>=2.0.35",
    "asyncpg>=0.29.0",
    "pydantic-settings>=2.5.0",
    "alembic>=1.13.0",
    "httpx>=0.27.0",
    "celery[redis]>=5.4.0",
    "pgvector>=0.3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
    "ruff>=0.6.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py312"
```

- [ ] **Step 2: Create Cargo.toml**

```toml
[package]
name = "supercool-nle"
version = "0.1.0"
edition = "2021"

[dependencies]
axum = "0.7"
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
uuid = { version = "1", features = ["v4"] }
tracing = "0.1"
tracing-subscriber = "0.3"
```

- [ ] **Step 3: Create app/config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "SUPERCOOL_"}

    database_url: str = "postgresql+asyncpg://supercool:supercool@localhost:5432/supercool"
    database_url_sync: str = "postgresql://supercool:supercool@localhost:5432/supercool"
    redis_url: str = "redis://localhost:6379/0"
    nle_url: str = "http://localhost:8080"
    google_api_key: str = ""
    openai_api_key: str = ""
    nvidia_api_key: str = ""
    llm_provider: str = "google"
    llm_fallback_enabled: bool = True


settings = Settings()
```

- [ ] **Step 4: Create app/main.py**

```python
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(
        title="SuperCool - AI Cinematic Studio",
        version="0.1.0",
    )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app
```

- [ ] **Step 5: Create tests/conftest.py**

```python
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

- [ ] **Step 6: Write failing test**

Create `tests/test_api/test_health.py`:

```python
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 7: Run test to verify it passes**

Run: `cd supercool && python -m pytest tests/test_api/test_health.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git init
git add pyproject.toml Cargo.toml app/ tests/
git commit -m "feat: project scaffolding with FastAPI app factory"
```

---

## Task 2: Database Layer

**Files:**
- Create: `app/db/__init__.py`
- Create: `app/db/database.py`
- Modify: `app/config.py` (add database settings)

**Interfaces:**
- Consumes: `settings` from config
- Produces: `engine`, `async_session`, `Base` declarative base

- [ ] **Step 1: Write failing test**

Create `tests/test_db/test_database.py`:

```python
import pytest
from sqlalchemy import text
from app.db.database import engine


async def test_engine_creation():
    assert engine is not None


async def test_database_connection():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_db/test_database.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Create app/db/database.py**

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_db/test_database.py -v`
Expected: PASS (requires running PostgreSQL)

- [ ] **Step 5: Commit**

```bash
git add app/db/ tests/test_db/
git commit -m "feat: async SQLAlchemy database layer"
```

---

## Task 3: Database Models

**Files:**
- Create: `app/models/__init__.py`
- Create: `app/models/project.py`
- Create: `app/models/character.py`
- Create: `app/models/scene.py`
- Create: `app/models/shot.py`
- Create: `app/models/render_job.py`

**Interfaces:**
- Consumes: `Base` from database
- Produces: `Project`, `Character`, `AnchorFace`, `Scene`, `Shot`, `RenderJob` ORM models

- [ ] **Step 1: Write failing test**

Create `tests/test_models/test_models.py`:

```python
import pytest
from app.models.project import Project
from app.models.character import Character, AnchorFace
from app.models.scene import Scene
from app.models.shot import Shot
from app.models.render_job import RenderJob


def test_project_model():
    p = Project(title="Test Film", description="A test")
    assert p.title == "Test Film"
    assert p.fps == 24
    assert p.target_resolution == "4K"


def test_character_model():
    c = Character(name="Boruto", locked_traits=["scar", "cape"])
    assert c.name == "Boruto"
    assert c.locked_traits == ["scar", "cape"]


def test_shot_model():
    s = Shot(prompt_text="A warrior stands", status="PENDING")
    assert s.status == "PENDING"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_models/test_models.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Create app/models/project.py**

```python
import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    target_resolution: Mapped[str] = mapped_column(String(20), default="4K")
    fps: Mapped[int] = mapped_column(Integer, default=24)
    aspect_ratio: Mapped[str] = mapped_column(String(10), default="16:9")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    characters = relationship("Character", back_populates="project", cascade="all, delete-orphan")
    scenes = relationship("Scene", back_populates="project", cascade="all, delete-orphan")
```

- [ ] **Step 4: Create app/models/character.py**

```python
import uuid
from datetime import datetime

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.database import Base


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    biography: Mapped[str | None] = mapped_column(Text)
    locked_traits: Mapped[list] = mapped_column(JSONB, default=list)
    voice_profile_id: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="characters")
    anchor_faces = relationship("AnchorFace", back_populates="character", cascade="all, delete-orphan")


class AnchorFace(Base):
    __tablename__ = "anchor_faces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"))
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    view_angle: Mapped[str | None] = mapped_column(String(50))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    character = relationship("Character", back_populates="anchor_faces")
```

- [ ] **Step 5: Create app/models/scene.py**

```python
import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class Scene(Base):
    __tablename__ = "scenes"
    __table_args__ = (UniqueConstraint("project_id", "scene_number"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    time_of_day: Mapped[str | None] = mapped_column(String(50))
    summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="scenes")
    shots = relationship("Shot", back_populates="scene", cascade="all, delete-orphan")
```

- [ ] **Step 6: Create app/models/shot.py**

```python
import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class Shot(Base):
    __tablename__ = "shots"
    __table_args__ = (UniqueConstraint("scene_id", "shot_number"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scene_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE"))
    shot_number: Mapped[int] = mapped_column(Integer, nullable=False)
    shot_type: Mapped[str | None] = mapped_column(String(50))
    motion_type: Mapped[str | None] = mapped_column(String(50))
    assigned_engine: Mapped[str | None] = mapped_column(String(50))
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    injected_prompt: Mapped[str | None] = mapped_column(Text)
    dialogue_text: Mapped[str | None] = mapped_column(Text)
    speaker_character_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    scene = relationship("Scene", back_populates="shots")
    render_jobs = relationship("RenderJob", back_populates="shot", cascade="all, delete-orphan")
```

- [ ] **Step 7: Create app/models/render_job.py**

```python
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Integer, Text, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class RenderJob(Base):
    __tablename__ = "render_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("shots.id", ondelete="CASCADE"))
    engine_name: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="QUEUED")
    output_url: Mapped[str | None] = mapped_column(Text)
    qa_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    qa_feedback: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    shot = relationship("Shot", back_populates="render_jobs")
```

- [ ] **Step 8: Create app/models/__init__.py**

```python
from app.models.project import Project
from app.models.character import Character, AnchorFace
from app.models.scene import Scene
from app.models.shot import Shot
from app.models.render_job import RenderJob

__all__ = ["Project", "Character", "AnchorFace", "Scene", "Shot", "RenderJob"]
```

- [ ] **Step 9: Run tests to verify they pass**

Run: `python -m pytest tests/test_models/test_models.py -v`
Expected: PASS

- [ ] **Step 10: Commit**

```bash
git add app/models/ tests/test_models/
git commit -m "feat: SQLAlchemy ORM models for all 6 tables"
```

---

## Task 4: Pydantic Schemas

**Files:**
- Create: `app/schemas/__init__.py`
- Create: `app/schemas/project.py`
- Create: `app/schemas/character.py`
- Create: `app/schemas/scene.py`
- Create: `app/schemas/shot.py`
- Create: `app/schemas/render_job.py`

**Interfaces:**
- Consumes: ORM models from Task 3
- Produces: Request/Response schemas for API

- [ ] **Step 1: Write failing test**

Create `tests/test_schemas/test_schemas.py`:

```python
from app.schemas.project import ProjectCreate, ProjectRead
from app.schemas.character import CharacterCreate, CharacterRead
from app.schemas.shot import ShotCreate, ShotRead


def test_project_create_schema():
    p = ProjectCreate(title="Test")
    assert p.title == "Test"
    assert p.fps == 24


def test_character_create_schema():
    c = CharacterCreate(name="Boruto", locked_traits=["scar"])
    assert c.name == "Boruto"
    assert c.locked_traits == ["scar"]


def test_shot_create_schema():
    s = ShotCreate(shot_number=1, prompt_text="A warrior")
    assert s.prompt_text == "A warrior"
    assert s.status == "PENDING"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_schemas/test_schemas.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Create all schema files**

`app/schemas/project.py`:
```python
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class ProjectCreate(BaseModel):
    title: str
    description: str | None = None
    target_resolution: str = "4K"
    fps: int = 24
    aspect_ratio: str = "16:9"


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    target_resolution: str
    fps: int
    aspect_ratio: str
    created_at: datetime
    updated_at: datetime
```

`app/schemas/character.py`:
```python
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class CharacterCreate(BaseModel):
    name: str
    biography: str | None = None
    locked_traits: list[str] = []
    voice_profile_id: str | None = None


class CharacterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    name: str
    biography: str | None
    locked_traits: list[str]
    voice_profile_id: str | None
    created_at: datetime


class AnchorFaceCreate(BaseModel):
    image_url: str
    view_angle: str | None = None
    is_primary: bool = False


class AnchorFaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    character_id: UUID
    image_url: str
    view_angle: str | None
    is_primary: bool
    created_at: datetime
```

`app/schemas/scene.py`:
```python
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class SceneCreate(BaseModel):
    scene_number: int
    title: str | None = None
    location: str | None = None
    time_of_day: str | None = None
    summary: str | None = None


class SceneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    scene_number: int
    title: str | None
    location: str | None
    time_of_day: str | None
    summary: str | None
    created_at: datetime
```

`app/schemas/shot.py`:
```python
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class ShotCreate(BaseModel):
    shot_number: int
    shot_type: str | None = None
    motion_type: str | None = None
    assigned_engine: str | None = None
    prompt_text: str
    dialogue_text: str | None = None
    speaker_character_id: UUID | None = None
    status: str = "PENDING"


class ShotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scene_id: UUID
    shot_number: int
    shot_type: str | None
    motion_type: str | None
    assigned_engine: str | None
    prompt_text: str
    injected_prompt: str | None
    dialogue_text: str | None
    speaker_character_id: UUID | None
    status: str
    created_at: datetime
```

`app/schemas/render_job.py`:
```python
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class RenderJobCreate(BaseModel):
    engine_name: str


class RenderJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    shot_id: UUID
    engine_name: str
    status: str
    output_url: str | None
    qa_score: Decimal | None
    qa_feedback: str | None
    retry_count: int
    created_at: datetime
    completed_at: datetime | None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_schemas/test_schemas.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/schemas/ tests/test_schemas/
git commit -m "feat: Pydantic request/response schemas"
```

---

## Task 5: API Routes - Projects

**Files:**
- Create: `app/api/__init__.py`
- Create: `app/api/deps.py`
- Create: `app/api/routes/__init__.py`
- Create: `app/api/routes/projects.py`
- Modify: `app/main.py` (add router)

**Interfaces:**
- Consumes: `get_db`, models, schemas
- Produces: CRUD endpoints for projects

- [ ] **Step 1: Write failing test**

Create `tests/test_api/test_projects.py`:

```python
import pytest


async def test_create_project(client):
    response = await client.post("/api/v1/projects", json={"title": "Test Film"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Film"
    assert data["fps"] == 24
    assert "id" in data


async def test_list_projects(client):
    await client.post("/api/v1/projects", json={"title": "Film 1"})
    await client.post("/api/v1/projects", json={"title": "Film 2"})
    response = await client.get("/api/v1/projects")
    assert response.status_code == 200
    assert len(response.json()) >= 2


async def test_get_project(client):
    create_resp = await client.post("/api/v1/projects", json={"title": "My Film"})
    project_id = create_resp.json()["id"]
    response = await client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "My Film"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_api/test_projects.py -v`
Expected: FAIL with 404

- [ ] **Step 3: Create app/api/deps.py**

```python
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import async_session


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with async_session() as session:
        yield session
```

- [ ] **Step 4: Create app/api/routes/projects.py**

```python
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectRead

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    project = Project(**data.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("", response_model=list[ProjectRead])
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project))
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(project_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Project not found")
    return project
```

- [ ] **Step 5: Update app/main.py**

```python
from fastapi import FastAPI
from app.api.routes import projects


def create_app() -> FastAPI:
    app = FastAPI(
        title="SuperCool - AI Cinematic Studio",
        version="0.1.0",
    )

    app.include_router(projects.router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/test_api/test_projects.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add app/api/ tests/test_api/test_projects.py app/main.py
git commit -m "feat: Project CRUD API endpoints"
```

---

## Task 6: API Routes - Scenes, Characters, Shots

**Files:**
- Create: `app/api/routes/scenes.py`
- Create: `app/api/routes/shots.py`
- Modify: `app/main.py` (add routers)

**Interfaces:**
- Consumes: models, schemas, get_db
- Produces: CRUD endpoints for scenes, characters, shots

- [ ] **Step 1: Write failing test**

Create `tests/test_api/test_scenes.py`:

```python
async def test_create_scene(client):
    proj = (await client.post("/api/v1/projects", json={"title": "F"})).json()
    response = await client.post(f"/api/v1/projects/{proj['id']}/scenes", json={
        "scene_number": 1,
        "title": "Opening",
        "location": "Forest"
    })
    assert response.status_code == 200
    assert response.json()["scene_number"] == 1


async def test_create_shot(client):
    proj = (await client.post("/api/v1/projects", json={"title": "F"})).json()
    scene = (await client.post(f"/api/v1/projects/{proj['id']}/scenes", json={"scene_number": 1})).json()
    response = await client.post(f"/api/v1/scenes/{scene['id']}/shots", json={
        "shot_number": 1,
        "prompt_text": "A warrior stands in the rain"
    })
    assert response.status_code == 200
    assert response.json()["prompt_text"] == "A warrior stands in the rain"
    assert response.json()["status"] == "PENDING"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_api/test_scenes.py -v`
Expected: FAIL with 404

- [ ] **Step 3: Create app/api/routes/scenes.py**

```python
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.scene import Scene
from app.models.character import Character, AnchorFace
from app.schemas.scene import SceneCreate, SceneRead
from app.schemas.character import CharacterCreate, CharacterRead, AnchorFaceCreate, AnchorFaceRead

router = APIRouter(tags=["scenes"])


@router.post("/projects/{project_id}/scenes", response_model=SceneRead)
async def create_scene(project_id: UUID, data: SceneCreate, db: AsyncSession = Depends(get_db)):
    scene = Scene(project_id=project_id, **data.model_dump())
    db.add(scene)
    await db.commit()
    await db.refresh(scene)
    return scene


@router.get("/projects/{project_id}/scenes", response_model=list[SceneRead])
async def list_scenes(project_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Scene).where(Scene.project_id == project_id))
    return result.scalars().all()


@router.post("/projects/{project_id}/characters", response_model=CharacterRead)
async def create_character(project_id: UUID, data: CharacterCreate, db: AsyncSession = Depends(get_db)):
    character = Character(project_id=project_id, **data.model_dump())
    db.add(character)
    await db.commit()
    await db.refresh(character)
    return character


@router.post("/characters/{character_id}/anchor-faces", response_model=AnchorFaceRead)
async def create_anchor_face(character_id: UUID, data: AnchorFaceCreate, db: AsyncSession = Depends(get_db)):
    face = AnchorFace(character_id=character_id, **data.model_dump())
    db.add(face)
    await db.commit()
    await db.refresh(face)
    return face
```

- [ ] **Step 4: Create app/api/routes/shots.py**

```python
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.shot import Shot
from app.schemas.shot import ShotCreate, ShotRead

router = APIRouter(tags=["shots"])


@router.post("/scenes/{scene_id}/shots", response_model=ShotRead)
async def create_shot(scene_id: UUID, data: ShotCreate, db: AsyncSession = Depends(get_db)):
    shot = Shot(scene_id=scene_id, **data.model_dump())
    db.add(shot)
    await db.commit()
    await db.refresh(shot)
    return shot


@router.get("/scenes/{scene_id}/shots", response_model=list[ShotRead])
async def list_shots(scene_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shot).where(Shot.scene_id == scene_id))
    return result.scalars().all()
```

- [ ] **Step 5: Update app/main.py**

```python
from fastapi import FastAPI
from app.api.routes import projects, scenes, shots


def create_app() -> FastAPI:
    app = FastAPI(
        title="SuperCool - AI Cinematic Studio",
        version="0.1.0",
    )

    app.include_router(projects.router, prefix="/api/v1")
    app.include_router(scenes.router, prefix="/api/v1")
    app.include_router(shots.router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/test_api/ -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add app/api/routes/scenes.py app/api/routes/shots.py app/main.py tests/test_api/test_scenes.py
git commit -m "feat: Scene, Character, Shot API endpoints"
```

---

## Task 7: Multi-Provider AI Abstraction

**Files:**
- Create: `app/providers/__init__.py`
- Create: `app/providers/base.py`
- Create: `app/providers/google.py`
- Create: `app/providers/openai.py`
- Create: `app/providers/nvidia.py`
- Create: `app/providers/registry.py`

**Interfaces:**
- Consumes: settings (API keys)
- Produces: `LLMProvider` ABC, `ProviderRegistry` with fallback

- [ ] **Step 1: Write failing test**

Create `tests/test_providers/test_registry.py`:

```python
import pytest
from app.providers.base import LLMProvider
from app.providers.registry import ProviderRegistry


def test_provider_registry_creation():
    registry = ProviderRegistry(providers={})
    assert registry is not None


def test_provider_interface():
    assert hasattr(LLMProvider, "extract_entities")
    assert hasattr(LLMProvider, "generate_prompt")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_providers/test_registry.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Create app/providers/base.py**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Entity:
    name: str
    entity_type: str  # "character", "location", "prop"
    traits: list[str]
    confidence: float


class LLMProvider(ABC):
    @abstractmethod
    async def extract_entities(self, text: str) -> list[Entity]:
        """Extract entities from text."""
        ...

    @abstractmethod
    async def generate_prompt(self, scene_description: str, characters: list[dict]) -> str:
        """Generate an enriched prompt from scene description."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is available."""
        ...
```

- [ ] **Step 4: Create app/providers/google.py**

```python
import httpx

from app.providers.base import LLMProvider, Entity
from app.config import settings


class GoogleProvider(LLMProvider):
    def __init__(self):
        self.api_key = settings.google_api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def extract_entities(self, text: str) -> list[Entity]:
        prompt = f"""Extract all named entities from this text. Return JSON array with:
        name, entity_type (character/location/prop), traits (list of strings), confidence (0-1).

        Text: {text}"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/models/gemini-2.0-flash:generateContent?key={self.api_key}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=30.0,
            )
            # Parse response (simplified)
            return []

    async def generate_prompt(self, scene_description: str, characters: list[dict]) -> str:
        char_info = "\n".join(f"- {c['name']}: {', '.join(c.get('locked_traits', []))}" for c in characters)
        prompt = f"""Generate a detailed cinematic prompt for this scene:
        {scene_description}

        Characters:
        {char_info}

        Include visual details, lighting, camera angle, mood."""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/models/gemini-2.0-flash:generateContent?key={self.api_key}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=30.0,
            )
            return response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")

    async def health_check(self) -> bool:
        return bool(self.api_key)
```

- [ ] **Step 5: Create app/providers/openai.py**

```python
import httpx

from app.providers.base import LLMProvider, Entity
from app.config import settings


class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.base_url = "https://api.openai.com/v1"

    async def extract_entities(self, text: str) -> list[Entity]:
        prompt = f"""Extract all named entities from this text. Return JSON array with:
        name, entity_type (character/location/prop), traits (list of strings), confidence (0-1).

        Text: {text}"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "gpt-4o",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                },
                timeout=30.0,
            )
            return []

    async def generate_prompt(self, scene_description: str, characters: list[dict]) -> str:
        char_info = "\n".join(f"- {c['name']}: {', '.join(c.get('locked_traits', []))}" for c in characters)
        prompt = f"""Generate a detailed cinematic prompt for this scene:
        {scene_description}

        Characters:
        {char_info}"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "gpt-4o",
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30.0,
            )
            return response.json()["choices"][0]["message"]["content"]

    async def health_check(self) -> bool:
        return bool(self.api_key)
```

- [ ] **Step 6: Create app/providers/nvidia.py**

```python
import httpx

from app.providers.base import LLMProvider, Entity
from app.config import settings


class NVIDIAProvider(LLMProvider):
    def __init__(self):
        self.api_key = settings.nvidia_api_key
        self.base_url = "https://integrate.api.nvidia.com/v1"

    async def extract_entities(self, text: str) -> list[Entity]:
        prompt = f"""Extract all named entities from this text. Return JSON array with:
        name, entity_type (character/location/prop), traits (list of strings), confidence (0-1).

        Text: {text}"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "meta/llama-3.1-8b-instruct",
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30.0,
            )
            return []

    async def generate_prompt(self, scene_description: str, characters: list[dict]) -> str:
        char_info = "\n".join(f"- {c['name']}: {', '.join(c.get('locked_traits', []))}" for c in characters)
        prompt = f"""Generate a detailed cinematic prompt for this scene:
        {scene_description}

        Characters:
        {char_info}"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "meta/llama-3.1-8b-instruct",
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30.0,
            )
            return response.json()["choices"][0]["message"]["content"]

    async def health_check(self) -> bool:
        return bool(self.api_key)
```

- [ ] **Step 7: Create app/providers/registry.py**

```python
from app.providers.base import LLMProvider
from app.providers.google import GoogleProvider
from app.providers.openai import OpenAIProvider
from app.providers.nvidia import NVIDIAProvider
from app.config import settings


class ProviderRegistry:
    def __init__(self, providers: dict[str, LLMProvider] | None = None):
        if providers is None:
            providers = {}
            if settings.google_api_key:
                providers["google"] = GoogleProvider()
            if settings.openai_api_key:
                providers["openai"] = OpenAIProvider()
            if settings.nvidia_api_key:
                providers["nvidia"] = NVIDIAProvider()
        self._providers = providers
        self._fallback_order = ["google", "openai", "nvidia"]

    def get_provider(self, name: str | None = None) -> LLMProvider | None:
        if name and name in self._providers:
            return self._providers[name]
        return None

    def get_fallback_provider(self) -> LLMProvider | None:
        for name in self._fallback_order:
            if name in self._providers:
                return self._providers[name]
        return None
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `python -m pytest tests/test_providers/test_registry.py -v`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add app/providers/ tests/test_providers/
git commit -m "feat: multi-provider AI abstraction (Google/OpenAI/NVIDIA)"
```

---

## Task 8: Story Bible Service

**Files:**
- Create: `app/services/__init__.py`
- Create: `app/services/story_bible.py`
- Create: `app/services/context_injector.py`

**Interfaces:**
- Consumes: ProviderRegistry, models
- Produces: `StoryBibleService`, `ContextInjector`

- [ ] **Step 1: Write failing test**

Create `tests/test_services/test_story_bible.py`:

```python
import pytest
from app.services.story_bible import StoryBibleService
from app.services.context_injector import ContextInjector


def test_context_injector_locked_traits():
    injector = ContextInjector()
    prompt = "Boruto stands in the rain"
    traits = ["fine vertical scar over right eye", "black cape with crimson lining"]
    result = injector.inject_locked_traits(prompt, traits)
    assert "scar" in result
    assert "cape" in result
    assert "Boruto" in result


def test_context_injector_negative_prompt():
    injector = ContextInjector()
    result = injector.get_negative_prompt()
    assert "2d anime" in result
    assert "cartoon" in result
    assert "extra fingers" in result


def test_context_injector_engine_routing():
    injector = ContextInjector()
    assert injector.detect_engine("dash forward and strike") == "SEEDANCE"
    assert injector.detect_engine("stare at the sunset") == "FLOW"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_services/test_story_bible.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Create app/services/context_injector.py**

```python
ACTION_KEYWORDS = {"dash", "dodge", "fight", "strike", "slash", "combat", "kick", "punch", "jump", "run"}
ATMOSPHERIC_KEYWORDS = {"stare", "speak", "sunset", "stand", "walk", "sit", "look", "gaze", "breathe"}

NEGATIVE_PROMPT = (
    "2d anime, cartoon, plastic skin, deformed scar, missing eye scar, "
    "altered cape color, extra fingers, distorted sword, face morphing between frames, "
    "60fps video look"
)

GLOBAL_STYLE = (
    "photorealistic skin texture, cinematic 35mm lens, moody sunset lighting, "
    "24fps film grain, 4k resolution"
)


class ContextInjector:
    def inject_locked_traits(self, prompt: str, traits: list[str]) -> str:
        if not traits:
            return prompt
        trait_str = ", ".join(traits)
        # Find character name (first word capitalized)
        words = prompt.split()
        for i, word in enumerate(words):
            if word[0].isupper() and i == 0:
                return f"{word} [{trait_str}] {' '.join(words[1:])}"
        return f"{prompt} [{trait_str}]"

    def inject_reference_tags(self, prompt: str, face_refs: list[dict]) -> str:
        if not face_refs:
            return prompt
        refs = " ".join(
            f"[INPUT_REF: {ref['image_url']}, ip_adapter_scale={ref.get('scale', 0.85)}]"
            for ref in face_refs
        )
        return f"{prompt} {refs}"

    def inject_global_style(self, prompt: str) -> str:
        return f"{prompt} ...{GLOBAL_STYLE}"

    def get_negative_prompt(self) -> str:
        return NEGATIVE_PROMPT

    def detect_engine(self, prompt: str) -> str:
        words = set(prompt.lower().split())
        if words & ACTION_KEYWORDS:
            return "SEEDANCE"
        return "FLOW"

    def get_engine_params(self, engine: str) -> dict:
        if engine == "SEEDANCE":
            return {"motion_scale": 1.4, "guidance_scale": 7.5, "ip_adapter_scale": 0.80}
        return {"motion_scale": 0.8, "guidance_scale": 6.0, "ip_adapter_scale": 0.90}

    def full_injection(self, prompt: str, traits: list[str], face_refs: list[dict] | None = None) -> dict:
        result = self.inject_locked_traits(prompt, traits)
        if face_refs:
            result = self.inject_reference_tags(result, face_refs)
        result = self.inject_global_style(result)
        engine = self.detect_engine(prompt)
        params = self.get_engine_params(engine)
        return {
            "prompt": result,
            "negative_prompt": self.get_negative_prompt(),
            "engine": engine,
            "engine_params": params,
        }
```

- [ ] **Step 4: Create app/services/story_bible.py**

```python
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.character import Character, AnchorFace
from app.models.shot import Shot
from app.providers.registry import ProviderRegistry
from app.services.context_injector import ContextInjector


class StoryBibleService:
    def __init__(self, db: AsyncSession, provider_registry: ProviderRegistry):
        self.db = db
        self.providers = provider_registry
        self.injector = ContextInjector()

    async def extract_entities(self, text: str) -> list[dict]:
        provider = self.providers.get_fallback_provider()
        if not provider:
            return []
        entities = await provider.extract_entities(text)
        return [{"name": e.name, "type": e.entity_type, "traits": e.traits} for e in entities]

    async def get_character_context(self, character_id: UUID) -> dict:
        result = await self.db.execute(select(Character).where(Character.id == character_id))
        character = result.scalar_one_or_none()
        if not character:
            return {}

        faces_result = await self.db.execute(
            select(AnchorFace).where(AnchorFace.character_id == character_id)
        )
        faces = faces_result.scalars().all()

        return {
            "name": character.name,
            "locked_traits": character.locked_traits or [],
            "face_refs": [
                {"image_url": f.image_url, "scale": 0.85 if f.is_primary else 0.75}
                for f in faces
            ],
        }

    async def inject_shot_prompt(self, shot_id: UUID) -> dict:
        result = await self.db.execute(select(Shot).where(Shot.id == shot_id))
        shot = result.scalar_one_or_none()
        if not shot:
            return {}

        # Get speaker character context if exists
        traits = []
        face_refs = []
        if shot.speaker_character_id:
            ctx = await self.get_character_context(shot.speaker_character_id)
            traits = ctx.get("locked_traits", [])
            face_refs = ctx.get("face_refs", [])

        injected = self.injector.full_injection(shot.prompt_text, traits, face_refs)

        # Update shot with injected prompt
        shot.injected_prompt = injected["prompt"]
        shot.assigned_engine = injected["engine"]
        await self.db.commit()

        return injected
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_services/test_story_bible.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/services/ tests/test_services/
git commit -m "feat: Story Bible service with context injection"
```

---

## Task 9: NLE Client (Python → Rust)

**Files:**
- Create: `app/services/nle_client.py`
- Create: `app/services/render_service.py`
- Create: `app/api/routes/render.py`

**Interfaces:**
- Consumes: httpx, settings.nle_url
- Produces: `NLEClient`, `RenderService`

- [ ] **Step 1: Write failing test**

Create `tests/test_services/test_nle_client.py`:

```python
import pytest
from app.services.nle_client import NLEClient


def test_nle_client_creation():
    client = NLEClient(base_url="http://localhost:8080")
    assert client.base_url == "http://localhost:8080"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_services/test_nle_client.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Create app/services/nle_client.py**

```python
import httpx

from app.config import settings


class NLEClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.nle_url

    async def health_check(self) -> bool:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{self.base_url}/nle/health", timeout=5.0)
                return resp.status_code == 200
            except Exception:
                return False

    async def concat(self, clips: list[str], output_path: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/nle/concat",
                json={"clips": clips, "output": output_path},
                timeout=120.0,
            )
            return resp.json()

    async def transcode(self, input_path: str, output_path: str, fps: int = 24) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/nle/transcode",
                json={"input": input_path, "output": output_path, "fps": fps},
                timeout=120.0,
            )
            return resp.json()

    async def mix_audio(self, tracks: list[str], output_path: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/nle/mix-audio",
                json={"tracks": tracks, "output": output_path},
                timeout=120.0,
            )
            return resp.json()

    async def pipeline(self, config: dict) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/nle/pipeline",
                json=config,
                timeout=600.0,
            )
            return resp.json()
```

- [ ] **Step 4: Create app/services/render_service.py**

```python
from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shot import Shot
from app.models.render_job import RenderJob
from app.services.nle_client import NLEClient
from app.services.story_bible import StoryBibleService
from app.providers.registry import ProviderRegistry


class RenderService:
    def __init__(self, db: AsyncSession, provider_registry: ProviderRegistry):
        self.db = db
        self.nle = NLEClient()
        self.story_bible = StoryBibleService(db, provider_registry)

    async def start_render(self, shot_id: UUID) -> RenderJob:
        # Inject prompt first
        await self.story_bible.inject_shot_prompt(shot_id)

        # Get shot
        result = await self.db.execute(select(Shot).where(Shot.id == shot_id))
        shot = result.scalar_one_or_none()
        if not shot:
            raise ValueError("Shot not found")

        # Create render job
        job = RenderJob(
            shot_id=shot_id,
            engine_name=shot.assigned_engine or "FLOW",
            status="QUEUED",
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        return job

    async def get_job_status(self, job_id: UUID) -> RenderJob | None:
        result = await self.db.execute(select(RenderJob).where(RenderJob.id == job_id))
        return result.scalar_one_or_none()
```

- [ ] **Step 5: Create app/api/routes/render.py**

```python
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.render_service import RenderService
from app.providers.registry import ProviderRegistry
from app.schemas.render_job import RenderJobCreate, RenderJobRead

router = APIRouter(tags=["render"])


def get_render_service(db: AsyncSession = Depends(get_db)) -> RenderService:
    return RenderService(db, ProviderRegistry())


@router.post("/shots/{shot_id}/render", response_model=RenderJobRead)
async def start_render(
    shot_id: UUID,
    service: RenderService = Depends(get_render_service),
):
    try:
        job = await service.start_render(shot_id)
        return job
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/jobs/{job_id}", response_model=RenderJobRead)
async def get_job(
    job_id: UUID,
    service: RenderService = Depends(get_render_service),
):
    job = await service.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
```

- [ ] **Step 6: Update app/main.py**

```python
from fastapi import FastAPI
from app.api.routes import projects, scenes, shots, render


def create_app() -> FastAPI:
    app = FastAPI(
        title="SuperCool - AI Cinematic Studio",
        version="0.1.0",
    )

    app.include_router(projects.router, prefix="/api/v1")
    app.include_router(scenes.router, prefix="/api/v1")
    app.include_router(shots.router, prefix="/api/v1")
    app.include_router(render.router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `python -m pytest tests/test_services/ -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add app/services/nle_client.py app/services/render_service.py app/api/routes/render.py app/main.py
git commit -m "feat: NLE client and render service"
```

---

## Task 10: Rust NLE Engine

**Files:**
- Create: `rust-nle/src/main.rs`
- Create: `rust-nle/src/lib.rs`
- Create: `rust-nle/src/ffmpeg/mod.rs`
- Create: `rust-nle/src/ffmpeg/concat.rs`
- Create: `rust-nle/src/ffmpeg/transcode.rs`
- Create: `rust-nle/src/ffmpeg/audio.rs`
- Create: `rust-nle/src/pipeline.rs`

**Interfaces:**
- Consumes: FFmpeg CLI via std::process::Command
- Produces: HTTP API at :8080

- [ ] **Step 1: Write failing test**

Create `rust-nle/src/lib.rs`:

```rust
pub mod ffmpeg;
pub mod pipeline;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_it_works() {
        assert_eq!(2 + 2, 4);
    }
}
```

Run: `cd rust-nle && cargo test`
Expected: PASS

- [ ] **Step 2: Create rust-nle/src/ffmpeg/mod.rs**

```rust
pub mod concat;
pub mod transcode;
pub mod audio;
```

- [ ] **Step 3: Create rust-nle/src/ffmpeg/concat.rs**

```rust
use std::process::Command;
use std::fs;

pub fn concat_stream_copy(clips: &[String], output: &str) -> Result<String, String> {
    // Create concat list file
    let list_path = format!("{}.txt", output);
    let content: String = clips.iter()
        .map(|c| format!("file '{}'", c))
        .collect::<Vec<_>>()
        .join("\n");
    fs::write(&list_path, content).map_err(|e| e.to_string())?;

    let output = Command::new("ffmpeg")
        .args(["-f", "concat", "-safe", "0", "-i", &list_path, "-c", "copy", output])
        .output()
        .map_err(|e| e.to_string())?;

    if output.status.success() {
        Ok(output.to_string_lossy().to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

pub fn concat_reencode(clips: &[String], output: &str) -> Result<String, String> {
    let n = clips.len();
    let mut cmd = Command::new("ffmpeg");
    for clip in clips {
        cmd.args(["-i", clip]);
    }

    let filter = format!(
        "{}concat=n={}:v=1:a=1[v][a]",
        clips.iter().enumerate().map(|(i, _)| format!("[{}:v][{}:a]", i, i)).collect::<String>(),
        n
    );

    cmd.args(["-filter_complex", &filter])
        .args(["-map", "[v]", "-map", "[a]"])
        .args(["-c:v", "libx264", "-crf", "18", "-preset", "fast"])
        .args(["-c:a", "aac", output]);

    let output = cmd.output().map_err(|e| e.to_string())?;
    if output.status.success() {
        Ok(output.to_string_lossy().to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}
```

- [ ] **Step 4: Create rust-nle/src/ffmpeg/transcode.rs**

```rust
use std::process::Command;

pub fn transcode_24fps(input: &str, output: &str) -> Result<String, String> {
    let output = Command::new("ffmpeg")
        .args(["-i", input])
        .args(["-vf", "fps=fps=24"])
        .args(["-c:v", "libx264", "-crf", "18", "-preset", "medium"])
        .args(["-c:a", "copy", output])
        .output()
        .map_err(|e| e.to_string())?;

    if output.status.success() {
        Ok(output.to_string_lossy().to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

pub fn transcode_custom(input: &str, output: &str, fps: i32, resolution: &str) -> Result<String, String> {
    let vf = format!("fps=fps={fps},scale={resolution}");
    let output = Command::new("ffmpeg")
        .args(["-i", input])
        .args(["-vf", &vf])
        .args(["-c:v", "libx264", "-crf", "18", "-preset", "medium"])
        .args(["-c:a", "copy", output])
        .output()
        .map_err(|e| e.to_string())?;

    if output.status.success() {
        Ok(output.to_string_lossy().to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}
```

- [ ] **Step 5: Create rust-nle/src/ffmpeg/audio.rs**

```rust
use std::process::Command;

pub fn mix_audio(tracks: &[String], output: &str) -> Result<String, String> {
    let mut cmd = Command::new("ffmpeg");
    for track in tracks {
        cmd.args(["-i", track]);
    }

    let filter = format!(
        "{}amix=inputs={}:duration=first:dropout_transition=2[aout]",
        tracks.iter().enumerate().map(|(i, _)| format!("[{}:a]", i)).collect::<String>(),
        tracks.len()
    );

    cmd.args(["-filter_complex", &filter])
        .args(["-map", "[aout]"])
        .args(["-c:a", "aac", "-b:a", "192k", output]);

    let output = cmd.output().map_err(|e| e.to_string())?;
    if output.status.success() {
        Ok(output.to_string_lossy().to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

pub fn ducking(video: &str, dialogue: &str, music: &str, output: &str) -> Result<String, String> {
    let filter = format!(
        "[2:a][1:a]sidechaincompress=threshold=0.08:ratio=12:attack=10:release=200[ducked]; \
         [1:a][ducked]amix=inputs=2:duration=first[aout]"
    );

    let output = Command::new("ffmpeg")
        .args(["-i", video])
        .args(["-i", dialogue])
        .args(["-i", music])
        .args(["-filter_complex", &filter])
        .args(["-map", "0:v", "-map", "[aout]"])
        .args(["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", output])
        .output()
        .map_err(|e| e.to_string())?;

    if output.status.success() {
        Ok(output.to_string_lossy().to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}
```

- [ ] **Step 6: Create rust-nle/src/pipeline.rs**

```rust
use crate::ffmpeg::{concat, transcode, audio};

#[derive(serde::Deserialize)]
pub struct PipelineConfig {
    pub clips: Vec<String>,
    pub audio_tracks: Vec<String>,
    pub output: String,
    pub fps: Option<i32>,
    pub resolution: Option<String>,
}

pub fn run_pipeline(config: &PipelineConfig) -> Result<String, String> {
    let temp_concat = format!("{}.concat.mp4", config.output);
    concat::concat_stream_copy(&config.clips, &temp_concat)?;

    let fps = config.fps.unwrap_or(24);
    let temp_transcoded = format!("{}.transcoded.mp4", config.output);
    transcode::transcode_24fps(&temp_concat, &temp_transcoded)?;

    if config.audio_tracks.len() == 2 {
        let dialogue = &config.audio_tracks[0];
        let music = &config.audio_tracks[1];
        audio::ducking(&temp_transcoded, dialogue, music, &config.output)?;
    } else if !config.audio_tracks.is_empty() {
        audio::mix_audio(&config.audio_tracks, &config.output)?;
    } else {
        std::fs::copy(&temp_transcoded, &config.output).map_err(|e| e.to_string())?;
    }

    // Cleanup temp files
    let _ = std::fs::remove_file(&temp_concat);
    let _ = std::fs::remove_file(&temp_transcoded);

    Ok(config.output.clone())
}
```

- [ ] **Step 7: Create rust-nle/src/main.rs**

```rust
use axum::{Router, Json, routing::{get, post}, extract::State};
use serde::{Deserialize, Serialize};
use std::sync::Arc;

mod ffmpeg;
mod pipeline;

#[derive(Clone)]
struct AppState {
    // placeholder for shared state
}

#[derive(Deserialize)]
struct ConcatRequest {
    clips: Vec<String>,
    output: String,
}

#[derive(Deserialize)]
struct TranscodeRequest {
    input: String,
    output: String,
    fps: Option<i32>,
}

#[derive(Deserialize)]
struct MixAudioRequest {
    tracks: Vec<String>,
    output: String,
}

#[derive(Serialize)]
struct HealthResponse {
    status: String,
    gpu_available: bool,
    ffmpeg_version: String,
}

async fn health() -> Json<HealthResponse> {
    let ffmpeg_version = std::process::Command::new("ffmpeg")
        .arg("-version")
        .output()
        .map(|o| String::from_utf8_lossy(&o.stdout).lines().next().unwrap_or("unknown").to_string())
        .unwrap_or("not found".to_string());

    Json(HealthResponse {
        status: "ok".to_string(),
        gpu_available: check_gpu(),
        ffmpeg_version,
    })
}

fn check_gpu() -> bool {
    std::process::Command::new("nvidia-smi")
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false)
}

async fn concat_handler(Json(req): Json<ConcatRequest>) -> Result<Json<serde_json::Value>, String> {
    ffmpeg::concat::concat_stream_copy(&req.clips, &req.output)
        .map(|_| Json(serde_json::json!({"status": "ok", "output": req.output})))
}

async fn transcode_handler(Json(req): Json<TranscodeRequest>) -> Result<Json<serde_json::Value>, String> {
    let fps = req.fps.unwrap_or(24);
    ffmpeg::transcode::transcode_24fps(&req.input, &req.output)
        .map(|_| Json(serde_json::json!({"status": "ok", "output": req.output})))
}

async fn mix_audio_handler(Json(req): Json<MixAudioRequest>) -> Result<Json<serde_json::Value>, String> {
    ffmpeg::audio::mix_audio(&req.tracks, &req.output)
        .map(|_| Json(serde_json::json!({"status": "ok", "output": req.output})))
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    let state = AppState {};

    let app = Router::new()
        .route("/nle/health", get(health))
        .route("/nle/concat", post(concat_handler))
        .route("/nle/transcode", post(transcode_handler))
        .route("/nle/mix-audio", post(mix_audio_handler))
        .with_state(Arc::new(state));

    let listener = tokio::net::TcpListener::bind("0.0.0.0:8080").await.unwrap();
    tracing::info!("NLE server listening on :8080");
    axum::serve(listener, app).await.unwrap();
}
```

- [ ] **Step 8: Build and test Rust NLE**

Run: `cd rust-nle && cargo build`
Expected: BUILD OK

- [ ] **Step 9: Commit**

```bash
git add rust-nle/
git commit -m "feat: Rust NLE engine with FFmpeg operations"
```

---

## Task 11: Alembic Migrations

**Files:**
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/script.py.mako`
- Create: `alembic/versions/001_initial.py`

**Interfaces:**
- Consumes: Base from database, all models
- Produces: Database migration

- [ ] **Step 1: Initialize Alembic**

Run: `cd supercool && uv run alembic init alembic`

- [ ] **Step 2: Configure alembic/env.py**

Update `alembic/env.py` to import Base and models:

```python
from app.db.database import Base
from app.models import *  # noqa: ensure all models registered
target_metadata = Base.metadata
```

- [ ] **Step 3: Generate initial migration**

Run: `uv run alembic revision --autogenerate -m "initial schema"`

- [ ] **Step 4: Apply migration**

Run: `uv run alembic upgrade head`

- [ ] **Step 5: Commit**

```bash
git add alembic/
git commit -m "feat: Alembic database migrations"
```

---

## Task 12: Integration Tests

**Files:**
- Create: `tests/test_api/test_integration.py`

**Interfaces:**
- Consumes: All previous tasks
- Produces: E2E API test

- [ ] **Step 1: Write integration test**

```python
import pytest


async def test_full_flow(client):
    # Create project
    proj = (await client.post("/api/v1/projects", json={"title": "Boruto TBV"})).json()

    # Create character
    char = (await client.post(f"/api/v1/projects/{proj['id']}/characters", json={
        "name": "Boruto Uzumaki",
        "locked_traits": ["fine vertical scar", "black cape"]
    })).json()

    # Create scene
    scene = (await client.post(f"/api/v1/projects/{proj['id']}/scenes", json={
        "scene_number": 1,
        "title": "The Village Gate",
        "location": "Konoha"
    })).json()

    # Create shot
    shot = (await client.post(f"/api/v1/scenes/{scene['id']}/shots", json={
        "shot_number": 1,
        "prompt_text": "Boruto dash forward and strike",
        "speaker_character_id": char["id"]
    })).json()

    # Start render
    job = (await client.post(f"/api/v1/shots/{shot['id']}/render")).json()

    # Check job status
    status = (await client.get(f"/api/v1/jobs/{job['id']}")).json()
    assert status["status"] == "QUEUED"
```

- [ ] **Step 2: Run tests**

Run: `python -m pytest tests/ -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_api/test_integration.py
git commit -m "feat: integration tests for full pipeline flow"
```

---

## Execution Options

Two execution approaches:

**1. Subagent-Driven (recommended)** — Fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session, batch execution with checkpoints.

Which approach?
