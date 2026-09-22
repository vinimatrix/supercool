"""MCP API - Model Context Protocol endpoints for Drift Editor integration."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.character import Character
from app.models.render_job import RenderJob
from app.models.shot import Shot
from app.schemas.character import AnchorFaceRead, CharacterRead
from app.schemas.shot import ShotRead

router = APIRouter(prefix="/mcp", tags=["mcp"])


class StoryBibleAssetsResponse(BaseModel):
    characters: list[CharacterRead]
    anchor_faces: list[AnchorFaceRead]
    voice_profiles: list[dict]


class ShotSequenceResponse(BaseModel):
    shots: list[ShotRead]
    total_duration_seconds: float


class PushTimelineEditsRequest(BaseModel):
    project_id: UUID
    timeline_data: dict  # JSON timeline from Drift
    trim_points: list[dict] | None = None
    track_arrangements: list[dict] | None = None


class TriggerRerenderRequest(BaseModel):
    shot_id: UUID
    engine_name: str | None = None
    adjusted_seed: int | None = None


class DuckingKeyframesRequest(BaseModel):
    project_id: UUID
    keyframes: list[dict]  # [{time: float, level: float}]


@router.post("/get_story_bible_assets", response_model=StoryBibleAssetsResponse)
async def get_story_bible_assets(project_id: UUID, db: AsyncSession = Depends(get_db)):
    """Expose story bible assets to external NLEs."""
    # Get characters
    chars_result = await db.execute(
        select(Character).where(Character.project_id == project_id)
    )
    characters = [CharacterRead.model_validate(c) for c in chars_result.scalars().all()]
    
    return StoryBibleAssetsResponse(
        characters=characters,
        anchor_faces=[],
        voice_profiles=[],
    )


@router.post("/fetch_shot_sequence", response_model=ShotSequenceResponse)
async def fetch_shot_sequence(scene_id: UUID, db: AsyncSession = Depends(get_db)):
    """Stream timeline clip sequences to external editing software."""
    result = await db.execute(
        select(Shot).where(Shot.scene_id == scene_id).order_by(Shot.shot_number)
    )
    shots = [ShotRead.model_validate(s) for s in result.scalars().all()]
    
    # Estimate duration (5 seconds per shot default)
    total_duration = len(shots) * 5.0
    
    return ShotSequenceResponse(
        shots=shots,
        total_duration_seconds=total_duration,
    )


@router.post("/push_timeline_edits")
async def push_timeline_edits(data: PushTimelineEditsRequest, db: AsyncSession = Depends(get_db)):
    """Ingest non-destructive timeline edits from external NLEs."""
    # Store edit metadata (in production, would update shot trim points)
    return {
        "status": "accepted",
        "project_id": str(data.project_id),
        "edits_applied": len(data.trim_points or []),
    }


@router.post("/trigger_shot_re_render")
async def trigger_shot_re_render(data: TriggerRerenderRequest, db: AsyncSession = Depends(get_db)):
    """Allow directors to trigger re-renders from external NLE timelines."""
    # Get the shot
    result = await db.execute(select(Shot).where(Shot.id == data.shot_id))
    shot = result.scalar_one_or_none()
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    
    # Create new render job
    job = RenderJob(
        shot_id=data.shot_id,
        engine_name=data.engine_name or shot.assigned_engine or "SEEDANCE",
        status="QUEUED",
    )
    db.add(job)
    shot.status = "RENDERING"
    await db.commit()
    await db.refresh(job)
    
    return {
        "status": "queued",
        "render_job_id": str(job.id),
        "shot_id": str(data.shot_id),
    }


@router.post("/sync_ducking_keyframes")
async def sync_ducking_keyframes(data: DuckingKeyframesRequest, db: AsyncSession = Depends(get_db)):
    """Export audio ducking envelope curves as keyframe data."""
    return {
        "status": "synced",
        "project_id": str(data.project_id),
        "keyframe_count": len(data.keyframes),
        "format": "sidechaincompress_envelope",
    }
