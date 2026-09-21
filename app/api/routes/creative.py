"""Creative Pipeline API - AI-powered editing endpoint."""

import os
import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.creative_pipeline import CreativePipeline, PipelineConfig

router = APIRouter(tags=["creative"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
WORKSPACE = BASE_DIR / "workspace"
WORKSPACE.mkdir(exist_ok=True)


class CreativeRenderRequest(BaseModel):
    clip_paths: list[str]
    scene_context: str = ""
    output_name: str = "render"
    master_volume: float = 1.0
    enable_audio: bool = True


class CreativeRenderResponse(BaseModel):
    final_output: str
    video_only: str
    duration: float
    shots: int
    mood: str
    music_crescendo: bool


@router.post("/creative/render", response_model=CreativeRenderResponse)
async def creative_render(data: CreativeRenderRequest):
    """Run the full AI creative pipeline on uploaded clips."""
    # Validate clips exist
    existing = []
    for path in data.clip_paths:
        full = Path(path)
        if not full.exists():
            # Try relative to workspace
            full = WORKSPACE / path
        if not full.exists():
            # Try with forward slashes
            full = WORKSPACE / path.replace("\\", "/")
        if full.exists():
            existing.append(str(full))
    
    if not existing:
        raise HTTPException(status_code=400, detail=f"No valid clips found. Searched: {data.clip_paths}")

    pipeline = CreativePipeline()
    config = PipelineConfig(
        workspace=str(WORKSPACE),
        output_name=data.output_name,
        scene_context=data.scene_context,
        master_volume=data.master_volume,
        enable_audio=data.enable_audio,
    )

    try:
        result = pipeline.run(existing, config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return CreativeRenderResponse(
        final_output=result["final_output"],
        video_only=result["video_only"],
        duration=result["duration"],
        shots=result["shots"],
        mood=result["mood"],
        music_crescendo=result["music_crescendo"],
    )


@router.get("/creative/workspace")
async def list_workspace():
    """List files in workspace."""
    files = []
    for f in sorted(WORKSPACE.rglob("*")):
        if f.is_file():
            files.append({
                "path": str(f.relative_to(WORKSPACE)),
                "size": f.stat().st_size,
                "type": f.suffix,
            })
    return files


@router.post("/creative/upload")
async def upload_clip(file_name: str, file_data: str):
    """Upload a clip to workspace (base64 encoded)."""
    import base64
    filepath = WORKSPACE / file_name
    with open(filepath, "wb") as f:
        f.write(base64.b64decode(file_data))
    return {"path": str(filepath), "size": os.path.getsize(filepath)}
