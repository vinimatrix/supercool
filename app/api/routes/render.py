from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.render_job import RenderJobRead
from app.services.nle_client import NLEClient
from app.services.render_service import RenderService

router = APIRouter(tags=["render"])


@router.post("/shots/{shot_id}/render", response_model=RenderJobRead)
async def start_render(
    shot_id: UUID,
    engine_name: str = "SEEDANCE",
    db: AsyncSession = Depends(get_db),
):
    """Start a render job for a shot."""
    service = RenderService(db)
    try:
        job = await service.start_render(str(shot_id), engine_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return job


@router.get("/jobs/{job_id}", response_model=RenderJobRead)
async def get_job(job_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a render job by ID."""
    service = RenderService(db)
    job = await service.get_job(str(job_id))
    if not job:
        raise HTTPException(status_code=404, detail="Render job not found")
    return job
