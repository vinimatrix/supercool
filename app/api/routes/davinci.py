"""DaVinci Resolve HTTP MCP API endpoints - control Resolve via HTTP JSON-RPC."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/davinci", tags=["DaVinci HTTP MCP"])


class CreateTracksRequest(BaseModel):
    video_track_names: list[str]
    audio_track_names: list[str]


class AppendClipRequest(BaseModel):
    media_path: str
    track_type: str
    track_index: int
    start_timecode: str
    clip_name: str


class DuckingEnvelopeRequest(BaseModel):
    target_track_index: int
    ducking_envelope: list[dict[str, Any]]


class QAMarkerRequest(BaseModel):
    timecode: str
    color: str
    note: str


class ExportRequest(BaseModel):
    preset_name: str
    output_folder: str


@router.get("/timeline")
async def get_active_timeline():
    """Get active timeline structure from DaVinci."""
    from app.services.davinci_mcp_client import get_davinci_http_client
    try:
        timeline = await get_davinci_http_client().get_active_timeline()
        return {
            "status": "ok",
            "data": {
                "name": timeline.name,
                "fps": timeline.fps,
                "start_timecode": timeline.start_timecode,
                "duration_frames": timeline.duration_frames,
                "tracks": timeline.tracks,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/tracks")
async def create_tracks(request: CreateTracksRequest):
    """Create track structure in DaVinci."""
    from app.services.davinci_mcp_client import get_davinci_http_client
    try:
        success = await get_davinci_http_client().create_tracks(
            request.video_track_names,
            request.audio_track_names,
        )
        return {"status": "ok" if success else "failed"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/clips")
async def append_clip(request: AppendClipRequest):
    """Append clip to timeline."""
    from app.services.davinci_mcp_client import get_davinci_http_client
    try:
        success = await get_davinci_http_client().append_clip(
            request.media_path,
            request.track_type,
            request.track_index,
            request.start_timecode,
            request.clip_name,
        )
        return {"status": "ok" if success else "failed"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/clips")
async def get_timeline_clips(track_type: str = "video", track_index: int = 1):
    """Get clips from timeline."""
    from app.services.davinci_mcp_client import get_davinci_http_client
    try:
        clips = await get_davinci_http_client().get_timeline_clips(track_type, track_index)
        return {
            "status": "ok",
            "data": [
                {
                    "clip_id": c.clip_id,
                    "shot_id": c.shot_id,
                    "media_path": c.media_path,
                    "duration_frames": c.duration_frames,
                    "qa_status": c.qa_status,
                }
                for c in clips
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/ducking")
async def sync_ducking(request: DuckingEnvelopeRequest):
    """Sync audio ducking keyframes to Fairlight."""
    from app.services.davinci_mcp_client import get_davinci_http_client
    try:
        success = await get_davinci_http_client().sync_ducking_keyframes(
            request.target_track_index,
            request.ducking_envelope,
        )
        return {"status": "ok" if success else "failed"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/markers")
async def add_qa_marker(request: QAMarkerRequest):
    """Add QA marker to timeline."""
    from app.services.davinci_mcp_client import get_davinci_http_client
    try:
        success = await get_davinci_http_client().add_qa_marker(
            request.timecode,
            request.color,
            request.note,
        )
        return {"status": "ok" if success else "failed"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/export")
async def export_master(request: ExportRequest):
    """Export final master from DaVinci."""
    from app.services.davinci_mcp_client import get_davinci_http_client
    try:
        success = await get_davinci_http_client().export_master(
            request.preset_name,
            request.output_folder,
        )
        return {"status": "ok" if success else "failed"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
