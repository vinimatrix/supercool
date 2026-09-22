"""Pipeline API Routes - Execute production pipeline for scenes."""

from datetime import datetime
from typing import Optional, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.scene import Scene
from app.models.shot import Shot
from app.models.shoot import Shoot
from app.services.production_pipeline import ProductionPipeline, PipelineResult

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


# ─── Schemas ────────────────────────────────────────────────────────────────

class ExecutePipelineRequest(BaseModel):
    """Request to execute production pipeline."""
    scene_id: UUID
    shot_ids: List[UUID]


class PipelineResponse(BaseModel):
    """Response from pipeline execution."""
    model_config = ConfigDict(from_attributes=True)
    
    scene_id: str
    shots_processed: int
    shoots_approved: int
    shoots_rejected: int
    final_video_path: Optional[str] = None
    timestamp: datetime
    details: dict


# ─── Endpoints ─────────────────────────────────────────────────────────────

@router.post("/execute", response_model=PipelineResponse)
async def execute_pipeline(
    request: ExecutePipelineRequest,
    db: AsyncSession = Depends(get_db)
):
    """Execute production pipeline for a scene."""
    # Fetch scene
    result = await db.execute(select(Scene).where(Scene.id == request.scene_id))
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    # Fetch shots
    shots = []
    for shot_id in request.shot_ids:
        result = await db.execute(select(Shot).where(Shot.id == shot_id))
        shot = result.scalar_one_or_none()
        if shot and shot.scene_id == scene.id:
            shots.append(shot)
    
    if not shots:
        raise HTTPException(status_code=404, detail="No valid shots found for scene")
    
    # Fetch shoots for each shot
    shoots_dict: Dict[str, List[Shoot]] = {}
    for shot in shots:
        result = await db.execute(select(Shoot).where(Shoot.shot_id == shot.id))
        shoots = result.scalars().all()
        shoots_dict[str(shot.id)] = list(shoots)
    
    # Execute pipeline
    pipeline = ProductionPipeline()
    pipeline_result = pipeline.execute_pipeline(scene, shots, shoots_dict)
    
    return pipeline_result