### Task 1: LipsyncJob model + migration + schemas + conftest

**Files:**
- Create: `app/models/lipsync_job.py`
- Modify: `app/models/__init__.py`
- Create: `alembic/versions/add_lipsync_jobs.py` (down_revision=`c0ffee123abc`)
- Create: `app/schemas/lipsync.py`
- Modify: `tests/conftest.py` (CREATE_LIPSYNC_JOBS + execute in `client` fixture)
- Test: `tests/test_models/test_lipsync_job.py`

**Interfaces:**
- Produces: `LipsyncJob` model; schemas `LipsyncJobRead`, `LipsyncJobCreate`, `LipsyncAssignRequest`, `MediaItem`; DDL `CREATE_LIPSYNC_JOBS`.

- [ ] **Step 1: Write failing model/schema test**

Create `tests/test_models/test_lipsync_job.py`:

```python
import app.models  # noqa: F401
from app.db.database import Base
from app.models.lipsync_job import LipsyncJob
from app.schemas.lipsync import LipsyncJobRead, MediaItem


def test_lipsync_job_registered_and_columns():
    assert "lipsync_jobs" in Base.metadata.tables
    cols = Base.metadata.tables["lipsync_jobs"].columns
    for name in (
        "id", "project_id", "status", "stage", "video_source", "trim_start",
        "trim_end", "audio_path", "output_path", "shot_id", "error",
        "created_at", "completed_at",
    ):
        assert name in cols, f"missing column {name}"


def test_lipsync_job_defaults():
    job = LipsyncJob(
        video_source="workspace/shots/a.mp4", trim_start=0.0, trim_end=5.0,
        audio_path="workspace/audio/b.wav",
    )
    assert job.status == "PENDING"
    assert job.stage is None


def test_schemas():
    item = MediaItem(path="workspace/shots/a.mp4", name="a.mp4", size=10, duration=3.5)
    assert item.duration == 3.5
    read = LipsyncJobRead.model_validate({
        "id": "00000000-0000-0000-0000-000000000001",
        "project_id": "00000000-0000-0000-0000-000000000002",
        "status": "PENDING", "stage": None,
        "video_source": "w/a.mp4", "trim_start": 0.0, "trim_end": 4.0,
        "audio_path": "w/b.wav", "output_path": None, "shot_id": None,
        "error": None, "created_at": "2026-01-01T00:00:00", "completed_at": None,
    })
    assert read.status == "PENDING"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_models/test_lipsync_job.py -v`
Expected: FAIL (`ModuleNotFoundError: app.models.lipsync_job`)

- [ ] **Step 3: Implement model**

Create `app/models/lipsync_job.py`:

```python
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base, get_uuid_type


class LipsyncJob(Base):
    __tablename__ = "lipsync_jobs"

    id: Mapped[uuid.UUID] = mapped_column(get_uuid_type(), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), ForeignKey("projects.id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    stage: Mapped[str | None] = mapped_column(String(50))
    video_source: Mapped[str] = mapped_column(Text, nullable=False)
    trim_start: Mapped[float] = mapped_column(Float, nullable=False)
    trim_end: Mapped[float] = mapped_column(Float, nullable=False)
    audio_path: Mapped[str] = mapped_column(Text, nullable=False)
    output_path: Mapped[str | None] = mapped_column(Text)
    shot_id: Mapped[uuid.UUID | None] = mapped_column(
        get_uuid_type(), ForeignKey("shots.id", ondelete="SET NULL")
    )
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
```

In `app/models/__init__.py` add `from app.models.lipsync_job import LipsyncJob` and `"LipsyncJob"` to `__all__`.

- [ ] **Step 4: Implement schemas**

Create `app/schemas/lipsync.py`:

```python
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MediaItem(BaseModel):
    path: str
    name: str
    size: int
    duration: float | None = None


class LipsyncJobCreate(BaseModel):
    project_id: UUID
    video_path: str
    trim_start: float
    trim_end: float
    audio_path: str
    shot_id: UUID | None = None


class LipsyncAssignRequest(BaseModel):
    shot_id: UUID


class LipsyncJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    status: str
    stage: str | None = None
    video_source: str
    trim_start: float
    trim_end: float
    audio_path: str
    output_path: str | None = None
    shot_id: UUID | None = None
    error: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
```

- [ ] **Step 5: Create Alembic migration**

First read `alembic/versions/fcae66ea5e4b_add_video_path_to_shots.py` to mirror its id/FK column style (PG UUID vs String). Create `alembic/versions/add_lipsync_jobs.py`:

```python
"""add lipsync_jobs table

Revision ID: d0d0face0001
Revises: c0ffee123abc
Create Date: 2026-09-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d0d0face0001"
down_revision: Union[str, Sequence[str], None] = "c0ffee123abc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lipsync_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="PENDING"),
        sa.Column("stage", sa.String(50), nullable=True),
        sa.Column("video_source", sa.Text(), nullable=False),
        sa.Column("trim_start", sa.Float(), nullable=False),
        sa.Column("trim_end", sa.Float(), nullable=False),
        sa.Column("audio_path", sa.Text(), nullable=False),
        sa.Column("output_path", sa.Text(), nullable=True),
        sa.Column("shot_id", sa.String(36), sa.ForeignKey("shots.id", ondelete="SET NULL"), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("lipsync_jobs")
```

- [ ] **Step 6: Update conftest**

In `tests/conftest.py` add after `CREATE_SHOOTS`:

```python
CREATE_LIPSYNC_JOBS = """
CREATE TABLE IF NOT EXISTS lipsync_jobs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING',
    stage VARCHAR(50),
    video_source TEXT NOT NULL,
    trim_start REAL NOT NULL,
    trim_end REAL NOT NULL,
    audio_path TEXT NOT NULL,
    output_path TEXT,
    shot_id TEXT,
    error TEXT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
)
"""
```

And in the `client` fixture after `CREATE_SHOOTS`: `await conn.execute(text(CREATE_LIPSYNC_JOBS))`.

- [ ] **Step 7: Run tests to verify pass**

Run: `python -m pytest tests/test_models/test_lipsync_job.py tests/test_api/test_reference_sheet.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add app/models/lipsync_job.py app/models/__init__.py app/schemas/lipsync.py alembic/versions/add_lipsync_jobs.py tests/conftest.py tests/test_models/test_lipsync_job.py
git commit -m "feat: add lipsync_jobs model, schema, migration"
```

