import sqlite3
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.lipsync_job import LipsyncJob
from app.services import lipsync_pipeline as lp
from tests.conftest import CREATE_LIPSYNC_JOBS


def test_probe_duration_uses_ffprobe():
    with patch("app.services.lipsync_pipeline.subprocess.run") as run:
        run.return_value = MagicMock(stdout='{"format": {"duration": "12.5"}}', returncode=0)
        assert lp.probe_duration("/x/v.mp4") == 12.5
        assert run.call_args.args[0][0] == "ffprobe"


def test_probe_duration_raises_on_ffprobe_failure():
    with patch("app.services.lipsync_pipeline.subprocess.run") as run:
        run.return_value = MagicMock(stdout="", returncode=1)
        with pytest.raises(ValueError, match="ffprobe failed"):
            lp.probe_duration("/x/v.mp4")


def test_trim_audio_shorter_than_selection_raises(tmp_path):
    audio = tmp_path / "short.wav"
    audio.write_bytes(b"RIFF")
    with patch.object(lp, "probe_duration", return_value=1.0):
        with pytest.raises(ValueError, match="audio shorter than selection"):
            lp.trim_media(str(audio), 0.0, 5.0, str(tmp_path / "out.wav"))


def test_trim_video_uses_stream_copy(tmp_path):
    src = tmp_path / "v.mp4"
    src.write_bytes(b"x")
    with patch("app.services.lipsync_pipeline.subprocess.run") as run:
        run.return_value = MagicMock(returncode=0)
        lp.trim_media(str(src), 1.0, 4.0, str(tmp_path / "out.mp4"))
    cmd = run.call_args.args[0]
    assert cmd[0] == "ffmpeg"
    assert "-ss" in cmd and "1.0" in cmd
    assert "-t" in cmd and "3.0" in cmd
    assert "-c" in cmd and "copy" in cmd


async def _memory_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.execute(text(CREATE_LIPSYNC_JOBS))
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _file_factory(db_path: Path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    async with engine.begin() as conn:
        await conn.execute(text(CREATE_LIPSYNC_JOBS))
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _insert_job(factory, **overrides):
    video_source = overrides.pop("video_source", "workspace/shots/v.mp4")
    audio_path = overrides.pop("audio_path", "workspace/audio/a.wav")
    async with factory() as session:
        job = LipsyncJob(
            project_id=uuid.uuid4(),
            video_source=video_source,
            trim_start=0.0,
            trim_end=3.0,
            audio_path=audio_path,
        )
        for key, value in overrides.items():
            setattr(job, key, value)
        session.add(job)
        await session.commit()
        return job.id


async def _reload(factory, job_id):
    async with factory() as session:
        return await session.get(LipsyncJob, job_id)


def _seed_media(project_root: Path):
    video = project_root / "workspace" / "shots" / "v.mp4"
    audio = project_root / "workspace" / "audio" / "a.wav"
    video.parent.mkdir(parents=True, exist_ok=True)
    audio.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"x")
    audio.write_bytes(b"x")


async def test_run_job_missing_job_is_noop():
    factory = await _memory_factory()
    await lp.run_job(str(uuid.uuid4()), factory)


async def test_run_job_marks_failed_on_error(tmp_path):
    factory = await _memory_factory()
    _seed_media(tmp_path)
    job_id = await _insert_job(factory)
    with patch.object(lp, "trim_media", side_effect=ValueError("audio shorter than selection")):
        await lp.run_job(str(job_id), factory, project_root=tmp_path)
    job = await _reload(factory, job_id)
    assert job.status == "FAILED"
    assert job.stage is None
    assert "audio shorter than selection" in job.error
    assert job.completed_at is not None


async def test_run_job_marks_failed_on_missing_file(tmp_path):
    factory = await _memory_factory()
    job_id = await _insert_job(factory, video_source="workspace/shots/nope.mp4")
    await lp.run_job(str(job_id), factory, project_root=tmp_path)
    job = await _reload(factory, job_id)
    assert job.status == "FAILED"
    assert "Missing file" in job.error


async def test_run_job_rejects_path_escaping_root(tmp_path):
    factory = await _memory_factory()
    job_id = await _insert_job(factory, video_source="../../etc/passwd")
    await lp.run_job(str(job_id), factory, project_root=tmp_path)
    job = await _reload(factory, job_id)
    assert job.status == "FAILED"
    assert "escapes" in job.error


async def test_run_job_marks_done(tmp_path):
    factory = await _memory_factory()
    _seed_media(tmp_path)
    job_id = await _insert_job(factory)
    output_abs = tmp_path / "workspace" / "lipsync" / f"lipsync_{job_id}.mp4"

    def fake_align(*_args, **_kwargs):
        output_abs.parent.mkdir(parents=True, exist_ok=True)
        output_abs.write_bytes(b"x")
        return str(output_abs)

    with (
        patch.object(lp, "trim_media", side_effect=lambda src, s, e, d: d),
        patch.object(lp, "MuseTalkClient") as client_cls,
    ):
        client_cls.return_value.align_lip_sync.side_effect = fake_align
        await lp.run_job(str(job_id), factory, project_root=tmp_path)
    job = await _reload(factory, job_id)
    assert job.status == "DONE"
    assert job.stage is None
    assert job.output_path == f"workspace/lipsync/lipsync_{job_id}.mp4"
    assert job.completed_at is not None
    kwargs = client_cls.return_value.align_lip_sync.call_args.kwargs
    assert kwargs["strict"] is True
    assert kwargs["output_filename"] == f"lipsync_{job_id}.mp4"


async def test_run_job_sets_stage_transitions(tmp_path):
    db_path = tmp_path / "jobs.db"
    factory = await _file_factory(db_path)
    _seed_media(tmp_path)
    job_id = await _insert_job(factory)
    stages = []

    def record_stage(_src, _s, _e, _d):
        with sqlite3.connect(db_path) as conn:
            row = conn.execute(
                "SELECT stage FROM lipsync_jobs WHERE id = ?", (job_id.hex,)
            ).fetchone()
        stages.append(row[0])
        return "unused"

    def record_align(*_args, **_kwargs):
        with sqlite3.connect(db_path) as conn:
            row = conn.execute(
                "SELECT stage FROM lipsync_jobs WHERE id = ?", (job_id.hex,)
            ).fetchone()
        stages.append(row[0])
        output_abs = tmp_path / "workspace" / "lipsync" / f"lipsync_{job_id}.mp4"
        output_abs.parent.mkdir(parents=True, exist_ok=True)
        output_abs.write_bytes(b"x")
        return str(output_abs)

    with (
        patch.object(lp, "trim_media", side_effect=record_stage),
        patch.object(lp, "MuseTalkClient") as client_cls,
    ):
        client_cls.return_value.align_lip_sync.side_effect = record_align
        await lp.run_job(str(job_id), factory, project_root=tmp_path)
    assert stages == ["TRIMMING", "TRIMMING", "INFERRING"]
