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

