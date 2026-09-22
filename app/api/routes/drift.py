"""Drift Integration API - Endpoints para integracion con Drift Editor via MCP."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.drift_client import DriftMCPClient

router = APIRouter(prefix="/drift", tags=["drift"])

drift_client = DriftMCPClient()


class ConnectRequest(BaseModel):
    port: int = 4731
    token: str | None = None


class ImportMediaRequest(BaseModel):
    paths: list[str]


class PlaceClipRequest(BaseModel):
    asset: str
    at: float = 0
    track: int = 0


class TransitionRequest(BaseModel):
    from_clip: str
    to_clip: str
    kind: str = "crossfade"
    duration: float = 0.5


class EditPlanClip(BaseModel):
    path: str | None = None
    duration: float = 5.0
    in_point: float | None = None
    out_point: float | None = None
    speed: float | None = 1.0
    color_grade: str | None = None
    volume: float | None = 1.0


class EditPlanTransition(BaseModel):
    from_clip: str
    to_clip: str
    type: str = "crossfade"
    duration: float = 0.5


class EditPlanRequest(BaseModel):
    clips: list[EditPlanClip]
    transitions: list[EditPlanTransition]


# === CONNECTION ===


@router.post("/connect")
async def connect_drift(req: ConnectRequest):
    success = await drift_client.connect(port=req.port, token=req.token)
    if success:
        return {"status": "connected", "port": req.port, "simulated": drift_client.simulated}
    raise HTTPException(status_code=503, detail="Cannot connect to Drift")


@router.get("/status")
async def drift_status():
    if drift_client.session:
        project = await drift_client.inspect()
        return {
            "connected": True,
            "simulated": drift_client.simulated,
            "port": drift_client.session.port,
            "project_loaded": project is not None and project.get("ok", False),
            "project_info": project,
        }
    return {"connected": False, "simulated": False}


@router.post("/disconnect")
async def disconnect_drift():
    await drift_client.close()
    return {"status": "disconnected"}


# === PROJECT ===


@router.get("/inspect")
async def inspect_project(clips: bool = True, detail: bool = True):
    result = await drift_client.inspect(clips=clips, detail=detail)
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.get("/catalog")
async def get_catalog():
    result = await drift_client.catalog()
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.get("/activity")
async def get_activity(start: float = 0, end: float = -1):
    result = await drift_client.activity(start=start, end=end)
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.get("/capture")
async def capture_frame(at: float = 0):
    result = await drift_client.capture(at=at)
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.get("/frames")
async def get_frames(at: list[float] = None, n: int = 12):
    result = await drift_client.frames(at=at, n=n)
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


# === MEDIA ===


@router.post("/import")
async def import_media(req: ImportMediaRequest):
    result = await drift_client.import_media(req.paths)
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.get("/assets")
async def list_assets():
    result = await drift_client.list_assets()
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


# === TIMELINE ===


@router.post("/track")
async def add_track(track_type: str = "video"):
    result = await drift_client.add_track(track_type)
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.post("/place")
async def place_clip(req: PlaceClipRequest):
    result = await drift_client.place_clip(req.asset, req.at, req.track)
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.post("/move")
async def move_clip(clip: str, to: float, track: int = None):
    result = await drift_client.move_clip(clip, to, track)
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.post("/split")
async def split_clip(clip: str, at: float):
    result = await drift_client.split_clip(clip, at)
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.delete("/clip/{clip_id}")
async def delete_clip(clip_id: str):
    result = await drift_client.delete_clip(clip_id)
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


# === EFFECTS ===


@router.get("/transitions")
async def list_transitions():
    result = await drift_client.list_transitions()
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.post("/transition")
async def add_transition(req: TransitionRequest):
    result = await drift_client.add_transition(
        req.from_clip, req.to_clip, req.kind, req.duration
    )
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.get("/effects")
async def list_effects():
    result = await drift_client.list_effects()
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.post("/effect")
async def add_effect(clip: str, effect_id: str):
    result = await drift_client.add_effect(clip, effect_id)
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.get("/audio-effects")
async def list_audio_effects():
    result = await drift_client.list_audio_effects()
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


# === CANVAS ===


@router.post("/volume")
async def set_volume(clip: str, volume: float):
    result = await drift_client.set_volume(clip, volume)
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.post("/fade")
async def set_fade(clip: str, fade_in: float = 0, fade_out: float = 0):
    result = await drift_client.set_fade(clip, fade_in, fade_out)
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.post("/speed")
async def set_speed(clip: str, speed: float):
    result = await drift_client.set_speed(clip, speed)
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


# === TEXT ===


@router.post("/text")
async def add_text(
    text: str,
    preset: str = "title",
    at: float = 0,
    track: int = -1,
    duration: float = 5.0,
):
    result = await drift_client.add_text(text, preset, at, track, duration)
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


# === AUDIO ===


@router.post("/detect-beats")
async def detect_beats(start: float = 0, duration: float = 30):
    result = await drift_client.detect_beats(start, duration)
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.post("/detect-scenes")
async def detect_scenes(clip: str):
    result = await drift_client.detect_scenes(clip)
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


# === PROJECT ===


@router.post("/setup")
async def set_project_setup(fps: int = 24, width: int = 3840, height: int = 2160):
    result = await drift_client.set_project_setup(fps, width, height)
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.post("/save")
async def save_project(path: str = None):
    result = await drift_client.save_project(path)
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.post("/export")
async def export_video(path: str, fps: int = 24, resolution: str = "4K"):
    scale_map = {"4K": 2160, "1080p": 1080, "720p": 720}
    height = scale_map.get(resolution, 2160)
    result = await drift_client.export_video(path, fps=fps, height=height)
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.get("/export-status")
async def export_status():
    result = await drift_client.export_status()
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


# === UNDO/REDO ===


@router.post("/undo")
async def undo():
    result = await drift_client.undo()
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.post("/redo")
async def redo():
    result = await drift_client.redo()
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.get("/history")
async def list_history(limit: int = 20):
    result = await drift_client.list_history(limit)
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


# === PLAYBACK ===


@router.post("/seek")
async def seek(time: float):
    result = await drift_client.seek(time)
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.post("/play")
async def play():
    result = await drift_client.play()
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


@router.post("/pause")
async def pause():
    result = await drift_client.pause()
    if result:
        return result
    raise HTTPException(status_code=503, detail="Drift not connected")


# === EDIT PLAN EXECUTION ===


@router.post("/execute-plan")
async def execute_edit_plan(plan: EditPlanRequest):
    try:
        if not drift_client.session:
            raise HTTPException(status_code=503, detail="Drift not connected")

        ops = []

        paths = [c.path for c in plan.clips if c.path]
        if paths:
            ops.append({"name": "import_media", "args": {"paths": paths}})

        project = await drift_client.inspect()
        if not project or not project.get("tracks"):
            ops.append({"name": "add_track", "args": {"type": "video"}})

        clip_ids = []
        current_time = 0.0

        for i, clip in enumerate(plan.clips):
            asset_ref = str(i)
            place_args = {"asset": asset_ref, "at": current_time, "track": 0}
            ops.append({"name": "place_clip", "args": place_args})
            clip_id = f"clip-{i}"
            clip_ids.append(clip_id)

            if clip.duration:
                ops.append({"name": "set_duration", "args": {"clip": clip_id, "duration": clip.duration}})

            if clip.in_point is not None or clip.out_point is not None:
                trim_args = {"clip": clip_id}
                if clip.in_point is not None:
                    trim_args["in"] = clip.in_point
                if clip.out_point is not None:
                    trim_args["out"] = clip.out_point
                ops.append({"name": "set_trim", "args": trim_args})

            if clip.volume is not None and clip.volume != 1.0:
                ops.append({"name": "set_volume", "args": {"clip": clip_id, "volume": clip.volume}})

            if clip.speed and clip.speed != 1.0:
                ops.append({"name": "set_clip_speed", "args": {"clip": clip_id, "speed": clip.speed}})

            current_time += clip.duration

        for trans in plan.transitions:
            from_idx = _extract_clip_index(trans.from_clip, clip_ids)
            to_idx = _extract_clip_index(trans.to_clip, clip_ids)
            if from_idx is not None and to_idx is not None:
                ops.append({
                    "name": "add_transition",
                    "args": {
                        "from": clip_ids[from_idx],
                        "to": clip_ids[to_idx],
                        "kind": trans.type,
                        "duration": trans.duration,
                    }
                })

        if ops:
            result = await drift_client.apply(ops)
            return {
                "status": "executed",
                "clips_placed": len([c for c in clip_ids if c]),
                "transitions_added": len(plan.transitions),
                "clip_ids": clip_ids,
                "mcp_result": result,
            }

        return {"status": "executed", "clips_placed": 0, "transitions_added": 0, "clip_ids": []}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _extract_clip_index(clip_ref: str, clip_ids: list[str]) -> int | None:
    if clip_ref.startswith("shot-"):
        try:
            idx = int(clip_ref.split("-")[-1]) - 1
            return idx if 0 <= idx < len(clip_ids) else None
        except ValueError:
            return None
    if clip_ref.startswith("clip-"):
        for i, cid in enumerate(clip_ids):
            if cid and cid in clip_ref:
                return i
        return None
    try:
        idx = int(clip_ref)
        return idx if 0 <= idx < len(clip_ids) else None
    except ValueError:
        for i, cid in enumerate(clip_ids):
            if cid == clip_ref:
                return i
        return None
