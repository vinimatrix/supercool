"""QA API - Visual quality control and verification."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.render_job import RenderJob
from app.models.shot import Shot
from app.schemas.render_job import RenderJobRead
from app.services.qa_director import QADirector

router = APIRouter(prefix="/qa", tags=["qa"])

# Initialize QA Director
qa_director = QADirector()


class QAVerifyRequest(BaseModel):
    shot_id: UUID
    render_job_id: UUID | None = None
    anchor_face_id: UUID | None = None


class QAResult(BaseModel):
    render_job_id: UUID
    shot_id: UUID
    qa_score: float | None
    status: str  # APPROVED, REJECTED, PENDING
    feedback: str | None


class QARetryRequest(BaseModel):
    shot_id: UUID
    render_job_id: UUID
    adjusted_seed: int | None = None
    ip_adapter_scale: float | None = None


@router.post("/verify", response_model=QAResult)
async def verify_shot(data: QAVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Run QA verification on a rendered shot."""
    # Get the render job
    if data.render_job_id:
        result = await db.execute(
            select(RenderJob).where(RenderJob.id == data.render_job_id)
        )
        job = result.scalar_one_or_none()
    else:
        # Get latest render job for the shot
        result = await db.execute(
            select(RenderJob)
            .where(RenderJob.shot_id == data.shot_id)
            .order_by(RenderJob.created_at.desc())
            .limit(1)
        )
        job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="No render job found")
    
    # Simulate QA scoring (in production, this would use CLIP/vision models)
    # For now, assign a score based on status
    qa_score = 0.85 if job.status == "COMPLETED" else None
    qa_status = "APPROVED" if qa_score and qa_score > 0.7 else "PENDING"
    feedback = "Auto-generated QA check" if qa_status == "APPROVED" else "Needs review"
    
    # Update render job
    job.qa_score = qa_score
    job.qa_feedback = feedback
    job.status = qa_status
    await db.commit()
    
    return QAResult(
        render_job_id=job.id,
        shot_id=data.shot_id,
        qa_score=qa_score,
        status=qa_status,
        feedback=feedback,
    )


@router.get("/results/{shot_id}", response_model=list[RenderJobRead])
async def get_qa_results(shot_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get QA verification history for a shot."""
    result = await db.execute(
        select(RenderJob)
        .where(RenderJob.shot_id == shot_id)
        .order_by(RenderJob.created_at.desc())
    )
    jobs = result.scalars().all()
    return [RenderJobRead.model_validate(j) for j in jobs]


@router.post("/retry", response_model=RenderJobRead)
async def retry_render(data: QARetryRequest, db: AsyncSession = Depends(get_db)):
    """Trigger re-render for a rejected shot with adjusted parameters."""
    # Get the original render job
    result = await db.execute(
        select(RenderJob).where(RenderJob.id == data.render_job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Render job not found")
    
    # Create new render job with retry
    new_job = RenderJob(
        shot_id=data.shot_id,
        engine_name=job.engine_name,
        status="QUEUED",
        retry_count=job.retry_count + 1,
    )
    db.add(new_job)
    
    # Update shot status
    shot_result = await db.execute(select(Shot).where(Shot.id == data.shot_id))
    shot = shot_result.scalar_one_or_none()
    if shot:
        shot.status = "RENDERING"
    
    await db.commit()
    await db.refresh(new_job)
    
    return RenderJobRead.model_validate(new_job)


# --- Qwen2-VL QA Director Endpoints ---


class EvaluateShootRequest(BaseModel):
    shoot_id: str
    video_path: str
    scene_context: dict
    anchor_face_vectors: Optional[List[List[float]]] = None
    shot_type: str = "close_up"


class QADirectorResponse(BaseModel):
    shoot_id: str
    status: str
    clip_score: float
    qwen_diagnosis: str
    keyframes_analyzed: int
    timestamp: datetime
    details: dict


class ThresholdsResponse(BaseModel):
    clip_threshold: float
    action_threshold: float


@router.post("/evaluate", response_model=QADirectorResponse)
async def evaluate_shoot(data: EvaluateShootRequest):
    """Evaluate a shoot with Qwen2-VL quality assurance."""
    result = qa_director.evaluate_shoot(
        shoot_id=data.shoot_id,
        video_path=data.video_path,
        scene_context=data.scene_context,
        anchor_face_vectors=data.anchor_face_vectors,
        shot_type=data.shot_type,
    )

    return QADirectorResponse(
        shoot_id=result.shoot_id,
        status=result.status,
        clip_score=result.clip_score,
        qwen_diagnosis=result.qwen_diagnosis,
        keyframes_analyzed=result.keyframes_analyzed,
        timestamp=result.timestamp,
        details=result.details,
    )


@router.get("/thresholds", response_model=ThresholdsResponse)
async def get_thresholds():
    """Get current QA thresholds."""
    return ThresholdsResponse(
        clip_threshold=qa_director.clip_threshold,
        action_threshold=qa_director.action_threshold,
    )
