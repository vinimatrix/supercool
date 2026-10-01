"""Lipsync job API: media listing/upload, async job lifecycle, assign-to-shot."""

import re
import uuid as uuid_mod
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.config import BASE_DIR
from app.db.database import async_session
from app.models.lipsync_job import LipsyncJob
from app.models.project import Project
from app.models.shot import Shot
from app.schemas.lipsync import (
    LipsyncAssignRequest,
    LipsyncJobCreate,
    LipsyncJobRead,
    MediaItem,
)
from app.services.lipsync_pipeline import probe_duration, run_job

router = APIRouter(tags=["lipsync"])

VIDEO_SUBDIRS = ("shots", "pipeline_output", "exports", "lipsync/sources")
VIDEO_TYPES = {
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "video/webm": ".webm",
    "video/x-matroska": ".mkv",
    "video/x-msvideo": ".avi",
}
AUDIO_TYPES = {
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/wave": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/flac": ".flac",
    "audio/x-flac": ".flac",
    "audio/aac": ".aac",
    "audio/ogg": ".ogg",
}
VIDEO_EXT = set(VIDEO_TYPES.values())
AUDIO_EXT = set(AUDIO_TYPES.values())
MAX_VIDEO_BYTES = 500 * 1024 * 1024
MAX_AUDIO_BYTES = 50 * 1024 * 1024
CHUNK_BYTES = 64 * 1024
# Multipart framing (boundaries + part headers) sits on top of the raw file bytes.
CONTENT_LENGTH_OVERHEAD = 16 * 1024


def _workspace_root() -> Path:
    return Path(BASE_DIR) / "workspace"


def _rel_posix(path: Path) -> str:
    return path.resolve().relative_to(Path(BASE_DIR).resolve()).as_posix()


def _resolve_media(relative: str) -> Path | None:
    """Resolve a client-supplied path; must land inside workspace/ and be a file."""
    base = Path(BASE_DIR).resolve()
    workspace = base / "workspace"
    candidate = Path(relative)
    resolved = (candidate if candidate.is_absolute() else base / candidate).resolve()
    if not resolved.is_relative_to(workspace):
        return None
    return resolved if resolved.is_file() else None


def _media_item(path: Path) -> MediaItem:
    duration = None
    if path.suffix.lower() in VIDEO_EXT:
        try:
            duration = probe_duration(path)
        except Exception:
            duration = None
    return MediaItem(
        path=_rel_posix(path),
        name=path.name,
        size=path.stat().st_size,
        duration=duration,
    )


def _check_content_length(request: Request, max_bytes: int, label: str) -> None:
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and (
        int(content_length) > max_bytes + CONTENT_LENGTH_OVERHEAD
    ):
        raise HTTPException(status_code=413, detail=f"{label} too large")


async def _read_limited(file: UploadFile, max_bytes: int, label: str) -> bytes:
    buf = bytearray()
    while True:
        chunk = await file.read(CHUNK_BYTES)
        if not chunk:
            break
        buf += chunk
        if len(buf) > max_bytes:
            raise HTTPException(status_code=413, detail=f"{label} too large")
    return bytes(buf)


async def _upload_media(
    request: Request,
    file: UploadFile,
    type_map: dict[str, str],
    max_bytes: int,
    dest_dir: Path,
    label: str,
) -> MediaItem:
    _check_content_length(request, max_bytes, label)
    extension = type_map.get(file.content_type or "")
    if extension is None:
        raise HTTPException(status_code=400, detail=f"Unsupported {label.lower()} type")
    content = await _read_limited(file, max_bytes, label)

    safe_stem = Path(file.filename or label).name
    safe_stem = re.sub(r"[^A-Za-z0-9._-]", "_", safe_stem) or label.lower()
    stem = Path(safe_stem).stem or label.lower()
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / f"{stem}{extension}"
    counter = 1
    while target.exists():
        target = dest_dir / f"{stem}_{counter}{extension}"
        counter += 1
    target.write_bytes(content)
    return _media_item(target)


@router.get("/lipsync/videos", response_model=list[MediaItem])
async def list_lipsync_videos(project_id: uuid_mod.UUID | None = None):
    """List workspace videos available for lipsync (workspace-scoped)."""
    workspace = _workspace_root()
    items = []
    for subdir in VIDEO_SUBDIRS:
        directory = workspace / subdir
        if not directory.is_dir():
            continue
        for entry in sorted(directory.iterdir(), key=lambda p: p.name.lower()):
            if entry.is_file() and entry.suffix.lower() in VIDEO_EXT:
                items.append(_media_item(entry))
    return items


@router.get("/lipsync/audios", response_model=list[MediaItem])
async def list_lipsync_audios(project_id: uuid_mod.UUID | None = None):
    """List workspace audio files available for lipsync."""
    directory = _workspace_root() / "audio"
    if not directory.is_dir():
        return []
    return [
        _media_item(entry)
        for entry in sorted(directory.iterdir(), key=lambda p: p.name.lower())
        if entry.is_file() and entry.suffix.lower() in AUDIO_EXT
    ]


@router.post("/lipsync/videos", response_model=MediaItem)
async def upload_lipsync_video(
    request: Request,
    file: UploadFile = File(...),
    project_id: uuid_mod.UUID | None = None,
):
    return await _upload_media(
        request, file, VIDEO_TYPES, MAX_VIDEO_BYTES,
        _workspace_root() / "lipsync" / "sources", "Video",
    )


@router.post("/lipsync/audios", response_model=MediaItem)
async def upload_lipsync_audio(
    request: Request,
    file: UploadFile = File(...),
    project_id: uuid_mod.UUID | None = None,
):
    return await _upload_media(
        request, file, AUDIO_TYPES, MAX_AUDIO_BYTES,
        _workspace_root() / "audio", "Audio",
    )


@router.post("/lipsync/jobs", status_code=201, response_model=LipsyncJobRead)
async def create_lipsync_job(
    data: LipsyncJobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    if data.trim_start < 0 or data.trim_end <= data.trim_start:
        raise HTTPException(
            status_code=422,
            detail="trim_end must be greater than trim_start (trim_start >= 0)",
        )
    project = await db.get(Project, data.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if data.shot_id:
        shot = await db.get(Shot, data.shot_id)
        if not shot:
            raise HTTPException(status_code=404, detail="Shot not found")

    video = _resolve_media(data.video_path)
    if video is None:
        raise HTTPException(status_code=400, detail="Video not found")
    if video.suffix.lower() not in VIDEO_EXT:
        raise HTTPException(status_code=400, detail="Unsupported video format")
    audio = _resolve_media(data.audio_path)
    if audio is None:
        raise HTTPException(status_code=400, detail="Audio not found")
    if audio.suffix.lower() not in AUDIO_EXT:
        raise HTTPException(status_code=400, detail="Unsupported audio format")

    try:
        video_duration = probe_duration(video)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if data.trim_end > video_duration + 0.5:
        raise HTTPException(
            status_code=422,
            detail=f"trim_end exceeds video duration ({video_duration:.2f}s)",
        )
    try:
        audio_duration = probe_duration(audio)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if audio_duration < (data.trim_end - data.trim_start) - 0.05:
        raise HTTPException(status_code=422, detail="audio shorter than selection")

    job = LipsyncJob(
        project_id=data.project_id,
        video_source=_rel_posix(video),
        trim_start=data.trim_start,
        trim_end=data.trim_end,
        audio_path=_rel_posix(audio),
        shot_id=data.shot_id,
        status="PENDING",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    background_tasks.add_task(run_job, str(job.id), async_session)
    return job


@router.get("/lipsync/jobs", response_model=list[LipsyncJobRead])
async def list_lipsync_jobs(project_id: uuid_mod.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LipsyncJob)
        .where(LipsyncJob.project_id == project_id)
        .order_by(LipsyncJob.created_at.desc())
    )
    return result.scalars().all()


@router.get("/lipsync/jobs/{job_id}", response_model=LipsyncJobRead)
async def get_lipsync_job(job_id: uuid_mod.UUID, db: AsyncSession = Depends(get_db)):
    job = await db.get(LipsyncJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/lipsync/jobs/{job_id}/assign", response_model=LipsyncJobRead)
async def assign_lipsync_job(
    job_id: uuid_mod.UUID,
    data: LipsyncAssignRequest,
    db: AsyncSession = Depends(get_db),
):
    job = await db.get(LipsyncJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    shot = await db.get(Shot, data.shot_id)
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    if job.status != "DONE" or not job.output_path:
        raise HTTPException(status_code=400, detail="Job not finished")

    shot.video_path = job.output_path
    shot.status = "CLIP_ASSIGNED"
    job.shot_id = shot.id
    await db.commit()
    await db.refresh(job)
    return job
