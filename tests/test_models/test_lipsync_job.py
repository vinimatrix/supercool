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
