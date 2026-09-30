# MuseTalk Lipsync Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Backend job API + async processing pipeline + new `lipsync` tab UI for selecting a video, trimming a portion, picking audio, and running MuseTalk lipsync with status polling, preview, and assign-to-shot.

**Architecture:** Approach 2 (approved): FastAPI `BackgroundTasks` + `asyncio.to_thread` for blocking ffmpeg/MuseTalk calls, DB-backed `lipsync_jobs` table polled every 2s by the frontend. New `lipsync` tab follows the youtube/drift panel pattern. Output at `workspace/lipsync/lipsync_<job_id>.mp4` served via the existing `/workspace` StaticFiles mount.

**Tech Stack:** FastAPI + SQLAlchemy async + pytest (aiosqlite), Alembic, ffmpeg/ffprobe subprocess, MuseTalk subprocess client, React 19 + TS + vitest (jsdom), oxlint.

## Global Constraints

- Job statuses: `PENDING | RUNNING | DONE | FAILED`; stages: `TRIMMING | INFERRING | FINALIZING` (stage `null` when not RUNNING).
- Trim validation: `trim_end > trim_start` and `trim_start >= 0` → **422**; `trim_end > video_duration + 0.5` → **422**; missing video/audio files → **400**; missing job/shot/project → **404**; assign requires job `DONE` → **400** otherwise.
- Audio shorter than trim selection → job `FAILED` with error containing `audio shorter than selection`.
- MuseTalk **strict mode**: raise on inference failure or missing output (existing lenient callers keep default `strict=False`).
- Output path stored as `workspace/lipsync/lipsync_<job_id>.mp4`; frontend URL `http://localhost:8000/${output_path}`.
- Poll: 2s interval, immediate first poll, stop on terminal status, cleanup on unmount, 3 consecutive network failures → show error and stop polling.
- Backend pytest command (baseline 127 passed, 3 pre-existing env-broken deselected):
  `python -m pytest tests/ -q --ignore=tests/test_providers/test_registry.py --deselect=tests/test_db/test_database.py::test_database_connection --deselect=tests/test_integration_local_analyzer.py::TestLocalAnalyzerIntegration::test_qwen_analyzer_init --deselect=tests/test_local/test_coordinator.py::TestLocalVideoCoordinator::test_analyze_shot_returns_dict`
- Frontend: `C:\Program Files\nodejs\npm.cmd run build` / `test` / `run lint` green in `frontend/`.
- No new frontend dependencies; no Celery/Redis/WebSocket; no Drift API key/config changes.
- Ruff line-length 100; snake_case fields on the wire (`trim_start`, `video_source`, `output_path`).
- Media listing scopes: videos from `workspace/{shots,pipeline_output,exports,lipsync/sources}`, audios from `workspace/audio`.

---

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

### Task 2: Settings additions + MuseTalk client strict mode

**Files:**
- Modify: `app/config.py`
- Modify: `app/services/musetalk_client.py`
- Test: `tests/test_services/test_musetalk_strict.py`

**Interfaces:**
- Produces: `settings.musetalk_dir: str` (default `""` → resolved against `BASE_DIR/musetalk`), `settings.musetalk_timeout: int` (default `3600`); `MuseTalkClient.align_lip_sync(..., strict: bool = False)` raising `RuntimeError` in strict mode.

- [ ] **Step 1: Write failing tests**

Create `tests/test_services/test_musetalk_strict.py`:

```python
from pathlib import Path
from unittest.mock import patch

import pytest

from app.config import settings
from app.services.musetalk_client import MuseTalkClient


def test_settings_musetalk_fields():
    assert hasattr(settings, "musetalk_dir")
    assert hasattr(settings, "musetalk_timeout")
    assert settings.musetalk_timeout > 0


def test_align_strict_raises_on_failed_inference(tmp_path):
    client = MuseTalkClient(musetalk_dir=str(tmp_path))
    video = tmp_path / "src.mp4"
    audio = tmp_path / "a.wav"
    video.write_bytes(b"x")
    audio.write_bytes(b"x")
    with patch.object(client, "_run_musetalk", return_value=(False, "", "boom")):
        with pytest.raises(RuntimeError, match="MuseTalk failed"):
            client.align_lip_sync(str(video), str(audio), {}, strict=True)


def test_align_strict_raises_when_output_missing(tmp_path):
    client = MuseTalkClient(musetalk_dir=str(tmp_path))
    video = tmp_path / "src.mp4"
    audio = tmp_path / "a.wav"
    video.write_bytes(b"x")
    audio.write_bytes(b"x")
    with patch.object(client, "_run_musetalk", return_value=(True, "", "")):
        with pytest.raises(RuntimeError, match="MuseTalk produced no output"):
            client.align_lip_sync(str(video), str(audio), {}, output_filename="out.mp4", strict=True)


def test_align_lenient_still_returns_on_failure(tmp_path):
    client = MuseTalkClient(musetalk_dir=str(tmp_path))
    video = tmp_path / "src.mp4"
    audio = tmp_path / "a.wav"
    video.write_bytes(b"x")
    audio.write_bytes(b"x")
    with patch.object(client, "_run_musetalk", return_value=(False, "", "boom")):
        result = client.align_lip_sync(str(video), str(audio), {})
        assert Path(result).exists()
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_services/test_musetalk_strict.py -v`
Expected: FAIL (`TypeError: unexpected keyword 'strict'` / missing settings attrs)

- [ ] **Step 3: Read current code, then implement**

First read `app/config.py` and `app/services/musetalk_client.py` in full (also confirm `_run_musetalk` return signature — adjust test/impl to match reality; the tests above assume `(success: bool, stdout: str, stderr: str)`).

- Add to `Settings`:
  ```python
  musetalk_dir: str = ""
  musetalk_timeout: int = 3600
  ```
- In `MuseTalkClient.align_lip_sync`, accept `strict: bool = False`. When inference reports failure: if strict → `raise RuntimeError(f"MuseTalk failed: {stderr or stdout}")`; else keep existing lenient source-copy behavior. When success but output missing: if strict → `raise RuntimeError("MuseTalk produced no output video")`; else keep existing behavior.
- Do **not** change existing call sites (`voice.py` keeps default lenient).

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest tests/test_services/test_musetalk_strict.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/config.py app/services/musetalk_client.py tests/test_services/test_musetalk_strict.py
git commit -m "feat: strict mode for MuseTalk client + lipsync settings"
```

### Task 3: Lipsync pipeline service (ffmpeg trim + job runner)

**Files:**
- Create: `app/services/lipsync_pipeline.py`
- Test: `tests/test_services/test_lipsync_pipeline.py`

**Interfaces:**
- Produces: `probe_duration(path) -> float`, `trim_media(src, start, end, dst) -> str`, `run_job_sync(job_id: str, session_factory, project_root: Path) -> None`, `async run_job(job_id, session_factory) -> None`.
- Consumes: `LipsyncJob`, `MuseTalkClient.align_lip_sync(strict=True)`, `settings.musetalk_timeout`.

- [ ] **Step 1: Write failing tests**

Create `tests/test_services/test_lipsync_pipeline.py`:

```python
import asyncio
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import text

from app.services import lipsync_pipeline as lp


def test_probe_duration_uses_ffprobe():
    with patch("subprocess.run") as run:
        run.return_value = MagicMock(stdout='{"format": {"duration": "12.5"}}', returncode=0)
        assert lp.probe_duration("/x/v.mp4") == 12.5
        assert run.call_args.args[0][0] == "ffprobe"


def test_trim_audio_shorter_than_selection_raises(tmp_path):
    audio = tmp_path / "short.wav"
    audio.write_bytes(b"RIFF")
    with patch.object(lp, "probe_duration", return_value=1.0):
        with pytest.raises(ValueError, match="audio shorter than selection"):
            lp.trim_media(str(audio), 0.0, 5.0, str(tmp_path / "out.wav"))


def _make_job_row(job_id="j1", status="PENDING", stage=None):
    return {
        "id": job_id, "status": status, "stage": stage,
        "video_source": "workspace/shots/v.mp4", "trim_start": 0.0, "trim_end": 3.0,
        "audio_path": "workspace/audio/a.wav", "output_path": None,
        "error": None,
    }


def test_run_job_sync_sets_failed_on_error():
    session_factory = MagicMock()
    session = MagicMock()
    session_factory.return_value.__enter__ = MagicMock(return_value=session)
    session_factory.return_value.__exit__ = MagicMock(return_value=False)

    def execute_scalars_first(stmt):
        return _make_job_row()

    session.execute_scalars.return_value.first.side_effect = execute_scalars_first
    session.commit = MagicMock()

    with (
        patch.object(lp, "probe_duration", side_effect=ValueError("audio shorter than selection")),
        patch.object(lp.asyncio, "sleep", new=MagicMock()),
    ):
        lp.run_job_sync("j1", session_factory, project_root=None)

    update = session.execute.call_args.args[0]
    params = update.compile().params if hasattr(update, "compile") else {}
    assert "FAILED" in str(update) or params.get("status") == "FAILED"


def test_run_job_async_delegates_to_thread():
    with patch.object(lp.asyncio, "to_thread", new=MagicMock(return_value=None)) as to_thread:
        asyncio.run(lp.run_job("abc", MagicMock()))
        to_thread.assert_called_once()
```

Note: the DB-assertion approach in `test_run_job_sync_sets_failed_on_error` is brittle — if awkward, simplify by patching `_load_job`/`_finish_job` helpers (recommended: structure `lipsync_pipeline.py` with thin `_load_job(session, job_id)` and `_finish_job(session, job_id, status, output_path=None, error=None)` helpers so tests can assert on those calls directly instead of compiling SQLAlchemy statements).

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_services/test_lipsync_pipeline.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: Implement `app/services/lipsync_pipeline.py`**

```python
import asyncio
import json
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable

from app.config import settings
from app.services.musetalk_client import MuseTalkClient

OUTPUT_DIR_RELATIVE = "workspace/lipsync"
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def probe_duration(path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise ValueError(f"ffprobe failed for {path}")
    data = json.loads(result.stdout or "{}")
    duration = float(data.get("format", {}).get("duration", 0.0))
    if duration <= 0:
        raise ValueError(f"could not determine duration of {path}")
    return duration


def trim_media(src: str, start: float, end: float, dst: str) -> str:
    if src.lower().endswith((".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg")):
        src_duration = probe_duration(src)
        if src_duration < (end - start) - 0.05:
            raise ValueError("audio shorter than selection")
        subprocess.run(
            ["ffmpeg", "-y", "-ss", str(start), "-t", str(end - start), "-i", src, dst],
            check=True, capture_output=True,
        )
    else:
        subprocess.run(
            ["ffmpeg", "-y", "-ss", str(start), "-to", str(end), "-i", src, "-c", "copy", dst],
            check=True, capture_output=True,
        )
    return dst
```

Then `run_job_sync(job_id, session_factory, project_root)`:

1. Open session; `_load_job` → row via `select(LipsyncJob).where(LipsyncJob.id == ...)`. If missing → return.
2. Set `status="RUNNING"`, `stage="TRIMMING"`; commit; flush errors → `_finish_job(..., status="FAILED", error=...)`.
3. Resolve `video_src = project_root / job.video_source`, `audio_src = project_root / job.audio_path` (guard: resolved path must stay under `project_root` else FAIL with `Path escapes workspace`).
4. Trims land in `project_root/WORKSPACE_ROOT/"tmp"/f"{job_id}_video.mp4"` and `f"{job_id}_audio.wav"` (create parent dirs; note for in-memory test DB `project_root=None` is only used in failure-before-paths tests — guard ordering so path resolution happens after the ValueError-prone audio trim probe **or** skip path guard when `project_root is None` in tests).
5. `stage="INFERRING"`; commit; `MuseTalkClient(musetalk_dir=...)` → `align_lip_sync(trimmed_video, trimmed_audio, config, output_filename=f"{job_id}.mp4", strict=True)` wrapped with `settings.musetalk_timeout` via `asyncio.wait_for` — but since this runs **in a thread**, use `subprocess` timeout already handled by client config; ensure client config passes timeout. On `Exception` → FAILED with `str(e)` truncated to 2000 chars.
6. `stage="FINALIZING"`; move output to `project_root/workspace/lipsync/lipsync_{job_id}.mp4`; `_finish_job(status="DONE", output_path="workspace/lipsync/lipsync_{job_id}.mp4")`.
7. Cleanup temp trims in `finally` (best-effort `unlink(missing_ok=True)`).
8. All status writes: set `completed_at=datetime.utcnow()` when terminal.

`async run_job(job_id: str, session_factory) -> None`: `await asyncio.to_thread(run_job_sync, job_id, session_factory, WORKSPACE_ROOT)` — module-level function so routes can monkeypatch `lipsync_pipeline.run_job`.

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest tests/test_services/test_lipsync_pipeline.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/lipsync_pipeline.py tests/test_services/test_lipsync_pipeline.py
git commit -m "feat: lipsync pipeline with ffmpeg trim and strict MuseTalk run"
```

### Task 4: API routes `/api/v1/lipsync/*`

**Files:**
- Create: `app/api/routes/lipsync.py`
- Modify: `app/main.py` (register router)
- Test: `tests/test_api/test_lipsync.py`

**Interfaces:**
- Produces (FastAPI):
  - `GET  /api/v1/lipsync/videos?project_id=` → `list[MediaItem]` (from `workspace/{shots,pipeline_output,exports,lipsync/sources}`)
  - `GET  /api/v1/lipsync/audios?project_id=` → `list[MediaItem]` (from `workspace/audio`)
  - `POST /api/v1/lipsync/videos?project_id=` multipart `file` → `MediaItem` (saved under `workspace/lipsync/sources/`)
  - `POST /api/v1/lipsync/audios?project_id=` multipart `file` → `MediaItem` (saved under `workspace/audio/`)
  - `POST /api/v1/lipsync/jobs` body `LipsyncJobCreate` → `201` `LipsyncJobRead`, enqueues `BackgroundTasks`
  - `GET  /api/v1/lipsync/jobs?project_id=` → `list[LipsyncJobRead]` (newest first)
  - `GET  /api/v1/lipsync/jobs/{job_id}` → `LipsyncJobRead`
  - `POST /api/v1/lipsync/jobs/{job_id}/assign` body `LipsyncAssignRequest` → `LipsyncJobRead`
- Consumes: `get_db`, `LipsyncJob`, `lipsync_pipeline.run_job` (module-level reference for monkeypatching).

- [ ] **Step 1: Write failing tests**

Create `tests/test_api/test_lipsync.py` covering:
1. `test_list_videos_and_audios` — seed `workspace/shots`/`workspace/audio` files via `tmp_path`-patched `WORKSPACE` root **or** `monkeypatch.setattr(lipsync_routes, "WORKSPACE_ROOT", tmp_path)`; assert names/sizes returned; duration present for `.mp4` (patch `probe_duration`).
2. `test_upload_audio_rejects_oversize` — 6 MB body → 413/400 (mirror `test_reference_sheet` upload-rejection style; first read that file for the exact pattern, including the early size check).
3. `test_create_job_happy_path` — `monkeypatch.setattr(lipsync_routes, "run_job", fake)` where `fake` is recorded async stub **and** routes must call `run_job` through a module-level name (`background_tasks.add_task(lipsync_routes.run_job, ...)` is not directly awaitable-assertable — instead assert response `status == "PENDING"` and that `fake_jobs.append` recorded the job id via patching `app.services.lipsync_pipeline.run_job` **before** import of route callables; simplest reliable approach: patch `app.api.routes.lipsync.run_job`).
4. `test_create_job_trims_invalid` — `trim_end <= trim_start` → 422.
5. `test_create_job_missing_files` — paths outside workspace / nonexistent → 400.
6. `test_get_job_404` — random uuid → 404.
7. `test_assign_job_requires_done` — create job (PENDING) → assign → 400; force `status="DONE"` in DB → assign → 200 with `shot_id` set; assign to nonexistent shot → 404.
8. `test_path_traversal_rejected` — `video_path: "../../etc/passwd"` → 400.

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_api/test_lipsync.py -v`
Expected: FAIL (404s — router not registered)

- [ ] **Step 3: Implement `app/api/routes/lipsync.py`**

Key implementation points:

```python
router = APIRouter(prefix="/api/v1/lipsync", tags=["lipsync"])

ALLOWED_VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv", ".avi"}
ALLOWED_AUDIO_EXT = {".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg"}
VIDEO_SUBDIRS = ("shots", "pipeline_output", "exports", Path("lipsync") / "sources")
MAX_UPLOAD_BYTES = 5 * 1024 * 1024 * 100  # 500 MB videos; audios reuse same helper with 50 MB cap


def _workspace_root() -> Path:  # module-level, monkeypatchable; resolves BASE_DIR/workspace
    ...

def _safe_resolve(rel_or_abs: str) -> Path | None:
    """Resolve under workspace root; return None if outside or nonexistent."""
    candidate = Path(rel_or_abs)
    root = _workspace_root().resolve()
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    if not resolved.is_relative_to(root):
        return None
    return resolved if resolved.is_file() else None


def _media_item(path: Path) -> MediaItem:
    duration = None
    if path.suffix.lower() in {".mp4", ".mov", ".webm", ".mkv", ".avi"}:
        try:
            from app.services.lipsync_pipeline import probe_duration
            duration = probe_duration(str(path))
        except Exception:
            duration = None
    return MediaItem(path=path.relative_to(_workspace_root()).as_posix(),
                     name=path.name, size=path.stat().st_size, duration=duration)
```

- List endpoints: iterate `VIDEO_SUBDIRS` / `audio`, `sorted` by name, swallow missing dirs.
- Upload endpoints: **early size check** (`await file.read(MAX+1)` then reject if longer — mirrors reference_sheet), suffix from filename **and** content-type mapping (derive extension safely; reject mismatched/unknown), save under the proper subdir with sanitized filename (`re.sub(r"[^A-Za-z0-9._-]", "_", name)`), then `_media_item` on the saved path.
- `create_job`: resolve `video_path`/`audio_path` with `_safe_resolve` → 400 if None; validate `trim_end > trim_start >= 0` → 422 (use `LipsyncJobCreate` with a model_validator **or** explicit check raising `HTTPException(422)`); `probe_duration(video)` → `trim_end > duration + 0.5` → 422; probe audio duration vs trim length → **422** with `detail="audio shorter than selection"` (fast-fail before enqueueing); optional `shot_id` → 404 if not found; insert job (`status="PENDING"`), commit, `background_tasks.add_task(run_job, str(job.id), async_session_factory)` where `run_job` is imported at module top: `from app.services.lipsync_pipeline import run_job` (so tests patch `app.api.routes.lipsync.run_job`); return `201`.
- `assign_job`: load job → 404; load shot → 404; `job.status != "DONE" or not job.output_path` → 400 `detail="job not finished"`; set `shot_id`, commit.

In `app/main.py`: `from app.api.routes import lipsync` in the import block and `app.include_router(lipsync.router)` next to the voice router.

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest tests/test_api/test_lipsync.py -q`
Expected: PASS

- [ ] **Step 5: Run full backend suite**

Run the Global Constraints pytest command.
Expected: PASS (≥ previous 127)

- [ ] **Step 6: Commit**

```bash
git add app/api/routes/lipsync.py app/main.py tests/test_api/test_lipsync.py
git commit -m "feat: lipsync API routes with job lifecycle"
```

### Task 5: Frontend API client + studio context/tab plumbing

**Files:**
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/hooks/useStudioApi.ts`
- Modify: `frontend/src/context/StudioContext.tsx`
- Modify: `frontend/src/test/App.test.tsx` (add `lipsyncApi` to `../api/client` mock factory)
- Test: extend `frontend/src/test/App.test.tsx` (tabs render check)

**Interfaces:**
- Produces:
  ```ts
  export interface LipsyncJob { id: string; project_id: string; status: 'PENDING'|'RUNNING'|'DONE'|'FAILED'; stage: 'TRIMMING'|'INFERRING'|'FINALIZING'|null; video_source: string; trim_start: number; trim_end: number; audio_path: string; output_path: string|null; shot_id: string|null; error: string|null; created_at: string; completed_at: string|null; }
  export interface MediaItem { path: string; name: string; size: number; duration: number|null; }
  export const lipsyncApi = {
    listVideos(projectId), listAudios(projectId),
    uploadVideo(projectId, file), uploadAudio(projectId, file),
    createJob(body), listJobs(projectId), getJob(id), assignJob(id, shotId),
  };
  ```
- `useStudioApi` additions: `createLipsyncJob(body: LipsyncJobCreate): Promise<LipsyncJob|null>` (POST, `setLoading`, toast on error, returns null on failure), `assignLipsyncJob(jobId, shotId): Promise<LipsyncJob|null>` (same pattern). Polling stays **inside the panel** (useEffect), not the hook.
- `StudioTab` union += `'lipsync'`.

- [ ] **Step 1: Write failing tests**

In `frontend/src/test/App.test.tsx`: add `lipsyncApi: { listVideos: vi.fn(...), ... }` to the existing `vi.mock('../api/client', ...)` factory (read the file first; all methods must be vi.fn since component imports them). Add/extend a test asserting a `Lip` tab button renders and (after `userEvent.click`) the lipsync panel heading appears.

- [ ] **Step 2: Run tests to verify failure**

Run: `& "C:\Program Files\nodejs\npm.cmd" test -- --run` in `frontend/`
Expected: FAIL (no `lipsyncApi` export / no Lip tab)

- [ ] **Step 3: Implement**

- `client.ts`: interfaces + `lipsyncApi` object using the existing `api` instance (`api.get<...>('/v1/lipsync/videos', {params:{project_id}})` — **mirror the exact param/typing conventions of neighboring `*Api` objects; read 2–3 of them first**). Uploads via `FormData` + `multipart/form-data`.
- `StudioContext.tsx`: `export type StudioTab = ... | 'lipsync'`.
- `useStudioApi.ts`: the two mutation helpers, copying the existing create-assignment pattern verbatim (same toast strings style, same `finally { setLoading(false) }`).

- [ ] **Step 4: Run tests to verify pass**

Run: `& "C:\Program Files\nodejs\npm.cmd" test -- --run` in `frontend/`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/client.ts frontend/src/hooks/useStudioApi.ts frontend/src/context/StudioContext.tsx frontend/src/test/App.test.tsx
git commit -m "feat: lipsync API client and studio context plumbing"
```

### Task 6: LipsyncPanel UI + tab wiring

**Files:**
- Create: `frontend/src/components/lipsync/LipsyncPanel.tsx`
- Modify: `frontend/src/components/layout/TabNavigator.tsx` (add `{ id: 'lipsync', label: 'Lip' }`)
- Modify: `frontend/src/components/layout/Sidebar.tsx` (render `LipsyncPanel` for `activeTab === 'lipsync'`)
- Test: `frontend/src/test/LipsyncPanel.test.tsx`

**Interfaces:**
- Consumes: `lipsyncApi`, `useStudioApi`, `useStudioContext` (`activeProject?.id`, shots for assign dropdown), `StudioTab`.
- Panel sections: (1) **Source** — radio: "Workspace video" (list + "Upload video…" button) | "Upload file"; (2) **Trim** — range/number inputs `trim_start`/`trim_end` + duration hint from `MediaItem.duration`, inline error if `trim_end <= trim_start` or beyond duration; (3) **Audio** — radio: "Workspace audio" (list + upload) | "Upload file"; (4) **Run** — disabled unless valid; (5) **Status** — status chip + stage label + error text; (6) **Preview** — `<video controls src={http://localhost:8000/${job.output_path}}>` when DONE; (7) **Assign** — shot `<select>` + button (enabled when DONE); (8) **History** — prior jobs list (click to select/preview).

- [ ] **Step 1: Write failing tests**

Create `frontend/src/test/LipsyncPanel.test.tsx`:
- Mock `../context/StudioContext` (`useStudioContext` → `{ activeProject: { id: 'p1' }, shots: [...] }`), `../hooks/useStudioApi` (`createLipsyncJob`, `assignLipsyncJob`, `setLoading`), `../api/client` (`lipsyncApi.listVideos/listAudios/listJobs` resolved fixtures).
- Mirror the `vi.mock` module-factory style from `frontend/src/test/DriftPanel.test.tsx` (read it first).
- Tests: renders lists from mocks; Run button disabled until valid selection+trim+audio; clicking Run calls `createLipsyncJob` with snake_case payload (`trim_start`/`trim_end` numbers); polling: with `vi.useFakeTimers()` + a job returning `RUNNING` then `DONE`, assert a second `getJob` call after advancing 2000ms; unmount cleanup stops polling; assign button calls `assignLipsyncJob`; FAILED job shows `job.error`.

- [ ] **Step 2: Run tests to verify failure**

Run: `& "C:\Program Files\nodejs\npm.cmd" test -- --run` in `frontend/`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement `LipsyncPanel.tsx`**

State: `videoList/audioList/jobs: MediaItem[]|LipsyncJob[]`, `videoSource/audioSource: 'workspace'|'upload'`, selected paths/files, `trimStart/trimEnd: string`, `job: LipsyncJob|null`, `error: string|null`, `assignShotId: string`.
- Load lists on mount when `activeProject?.id` set (`Promise.all`), plus `lipsyncApi.listJobs`.
- Run handler: upload files first if in upload mode (via `lipsyncApi.uploadVideo/uploadAudio`), then `createLipsyncJob({...snake_case})`, store returned job, start polling.
- Polling effect: `if (!job || terminal) return;` `const t = setInterval(async () => { try { const next = await lipsyncApi.getJob(job.id); setJob(next); if terminal clearInterval } catch (e) { failCount++; if (failCount >= 3) { setError(...); clearInterval } } }, 2000); return () => clearInterval(t);` — immediate first poll via `void pollOnce()` before interval.
- Keep all JSX inline in this one component (matches Drift/youtube panel conventions); reuse existing Tailwind utility classes from sibling panels — read `DriftPanel.tsx` or the youtube panel before writing styles.
- Loading/success wired to `setLoading` from `useStudioApi` only for the create/assign mutations (list loads keep local `loading` state to avoid global spinner churn).

- [ ] **Step 4: Wire tab**

- `TabNavigator.tsx`: insert `{ id: 'lipsync', label: 'Lip' }` in the tabs array (position: after `drift` / alongside existing tabs — read file and keep grouping consistent).
- `Sidebar.tsx`: `case 'lipsync': return <LipsyncPanel />;` in the existing switch (import at top).

- [ ] **Step 5: Run tests + build + lint**

Run in `frontend/`: `npm test -- --run`, `npm run build`, `npm run lint`
Expected: all PASS (build may show chunk-size warning — pre-existing, ignore)

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/lipsync frontend/src/components/layout/TabNavigator.tsx frontend/src/components/layout/Sidebar.tsx frontend/src/test/LipsyncPanel.test.tsx
git commit -m "feat: lipsync tab with trim, poll, preview, assign"
```

### Task 7: Full verification + manual smoke

**Files:**
- No new code (fixes allowed wherever prior tasks left issues).

- [ ] **Step 1: Backend full suite**

Run Global Constraints pytest command.
Expected: all PASS, ≥ 127 passed, only the 3 known-env deselections skipped.

- [ ] **Step 2: Frontend full suite**

Run in `frontend/`: `npm test -- --run`, `npm run build`, `npm run lint`
Expected: PASS; only pre-existing oxlint warnings.

- [ ] **Step 3: Ruff**

Run: `python -m ruff check app tests`
Expected: PASS (line-length 100).

- [ ] **Step 4: Manual API smoke (uvicorn + curl/httpx)**

- Start server: activate venv, `python -m uvicorn app.main:app --port 8000`.
- `POST /api/v1/lipsync/jobs` with a real project id + existing workspace video/audio → expect 201 `PENDING`.
- Poll `GET /api/v1/lipsync/jobs/{id}` → transitions to `RUNNING`/`FAILED` (MuseTalk likely absent locally → job must FAIL with a `MuseTalk failed:`/`produced no output` error, **not** hang or 500) or `DONE` if models present.
- Verify failed-job row still retrievable via list endpoint.
- `GET /api/v1/lipsync/videos` returns the workspace listing.
- Stop server.

- [ ] **Step 5: Manual UI smoke**

- `npm run dev` + backend; open app → Lip tab visible; lists load; run a job → status chip advances or shows error; preview renders only on DONE; assign flow blocked until DONE.

- [ ] **Step 6: Fix any failures** (return to the owning task; re-run its tests)

- [ ] **Step 7: Final commit (if fixes were made)**

```bash
git add -u
git commit -m "fix: lipsync verification fixes"
```

---

## Execution Notes

- Order: 1 → 2 → 3 → 4 → 5 → 6 → 7. Tasks 1–4 are backend (sequential, shared DB/router state); Tasks 5–6 are frontend (depend on 4's route shapes); 7 last.
- Dispatch each task with `superpowers:subagent-driven-development`; use `task-brief` scripts to generate briefs from this file (tasks are H2 `### Task N:` headings).
- If a test assumes a helper shape that doesn't match reality (e.g. `_run_musetalk` return tuple), **adjust the test to match the real signature before implementing** — the plan's snippets are directional; the spec `docs/superpowers/specs/2026-09-30-musetalk-lipsync-design.md` is authoritative on behavior (statuses, error semantics, endpoints).
- New test files: `git add -f` (repo `.gitignore` pattern `test_*.py` silently ignores them).

