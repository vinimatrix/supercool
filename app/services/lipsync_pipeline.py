import asyncio
import json
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import BASE_DIR, settings
from app.models.lipsync_job import LipsyncJob
from app.services.musetalk_client import LipSyncConfig, MuseTalkClient

OUTPUT_DIR_RELATIVE = "workspace/lipsync"
AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg"}
MAX_ERROR_LEN = 2000


def probe_duration(path: str | Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"ffprobe failed for {path}")
    data = json.loads(result.stdout or "{}")
    duration = float(data.get("format", {}).get("duration", 0.0))
    if duration <= 0:
        raise ValueError(f"could not determine duration of {path}")
    return duration


def trim_media(src: str | Path, start: float, end: float, dst: str | Path) -> str:
    src = str(src)
    dst = str(dst)
    duration = end - start
    if Path(src).suffix.lower() in AUDIO_EXTENSIONS:
        src_duration = probe_duration(src)
        if src_duration < duration - 0.05:
            raise ValueError("audio shorter than selection")
        subprocess.run(
            ["ffmpeg", "-y", "-ss", str(start), "-t", str(duration), "-i", src, dst],
            check=True,
            capture_output=True,
        )
    else:
        subprocess.run(
            ["ffmpeg", "-y", "-ss", str(start), "-t", str(duration), "-i", src, "-c", "copy", dst],
            check=True,
            capture_output=True,
        )
    return dst


def _resolve_under(project_root: Path, relative: str) -> Path:
    candidate = Path(relative)
    root = project_root.resolve()
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"Path escapes workspace: {relative}")
    if not resolved.is_file():
        raise FileNotFoundError(f"Missing file: {relative}")
    return resolved


async def run_job(
    job_id: str,
    session_factory: Any,
    project_root: Path | None = None,
) -> None:
    """Run one lipsync job to completion. Designed for FastAPI BackgroundTasks.

    DB operations are awaited on the event loop; blocking ffmpeg/MuseTalk work
    is dispatched with asyncio.to_thread.
    """
    root = project_root if project_root is not None else BASE_DIR
    try:
        uid = uuid.UUID(job_id)
    except ValueError:
        return

    tmp_files: list[Path] = []
    try:
        async with session_factory() as session:
            job = await session.get(LipsyncJob, uid)
            if job is None:
                return
            try:
                job.status = "RUNNING"
                job.stage = "TRIMMING"
                await session.commit()

                video_src = _resolve_under(root, job.video_source)
                audio_src = _resolve_under(root, job.audio_path)

                tmp_dir = root / OUTPUT_DIR_RELATIVE / "tmp"
                await asyncio.to_thread(tmp_dir.mkdir, parents=True, exist_ok=True)
                trimmed_video = tmp_dir / f"{job_id}_video{video_src.suffix or '.mp4'}"
                trimmed_audio = tmp_dir / f"{job_id}_audio.wav"
                tmp_files.extend([trimmed_video, trimmed_audio])

                await asyncio.to_thread(
                    trim_media, video_src, job.trim_start, job.trim_end, trimmed_video
                )
                await asyncio.to_thread(
                    trim_media, audio_src, job.trim_start, job.trim_end, trimmed_audio
                )

                job.stage = "INFERRING"
                await session.commit()

                output_rel = f"{OUTPUT_DIR_RELATIVE}/lipsync_{job_id}.mp4"
                output_abs = root / output_rel
                await asyncio.to_thread(output_abs.parent.mkdir, parents=True, exist_ok=True)

                def _infer() -> str:
                    client = MuseTalkClient(musetalk_dir=settings.musetalk_dir or None)
                    client.output_dir = output_abs.parent
                    return client.align_lip_sync(
                        str(trimmed_video),
                        str(trimmed_audio),
                        LipSyncConfig(),
                        output_filename=output_abs.name,
                        strict=True,
                    )

                await asyncio.to_thread(_infer)
                if not output_abs.is_file():
                    raise RuntimeError("MuseTalk produced no output video")

                job.stage = "FINALIZING"
                await session.commit()

                job.status = "DONE"
                job.stage = None
                job.output_path = output_rel
                job.error = None
                job.completed_at = datetime.utcnow()
                await session.commit()
            except Exception as exc:
                await session.rollback()
                job.status = "FAILED"
                job.stage = None
                job.error = str(exc)[:MAX_ERROR_LEN]
                job.completed_at = datetime.utcnow()
                await session.commit()
    finally:
        for tmp_file in tmp_files:
            try:
                tmp_file.unlink(missing_ok=True)
            except OSError:
                pass
