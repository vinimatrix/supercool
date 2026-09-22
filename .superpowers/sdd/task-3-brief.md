# Task 3: Database Models

**Files:**
- Create: `app/models/__init__.py`
- Create: `app/models/project.py`
- Create: `app/models/character.py`
- Create: `app/models/scene.py`
- Create: `app/models/shot.py`
- Create: `app/models/render_job.py`

**Interfaces:**
- Consumes: `Base` from `app.db.database`
- Produces: `Project`, `Character`, `AnchorFace`, `Scene`, `Shot`, `RenderJob` ORM models

## Step 1: Write failing test

Create `tests/test_models/__init__.py` (empty) and `tests/test_models/test_models.py`:

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

## Step 2: Run test to verify it fails

Run: `python -m pytest tests/test_models/test_models.py -v`
Expected: FAIL with ImportError

## Step 3: Create all model files

Create `app/models/__init__.py`:
```python
from app.models.project import Project
from app.models.character import Character, AnchorFace
from app.models.scene import Scene
from app.models.shot import Shot
from app.models.render_job import RenderJob

__all__ = ["Project", "Character", "AnchorFace", "Scene", "Shot", "RenderJob"]
```

Create `app/models/project.py`:
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

Create `app/models/character.py`:
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

Create `app/models/scene.py`:
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

Create `app/models/shot.py`:
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

Create `app/models/render_job.py`:
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

## Step 4: Run tests to verify they pass

Run: `python -m pytest tests/test_models/test_models.py -v`
Expected: PASS

## Step 5: Commit

```bash
git add app/models/ tests/test_models/
git commit -m "feat: SQLAlchemy ORM models for all 6 tables"
```
