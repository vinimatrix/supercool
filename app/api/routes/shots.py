from uuid import UUID
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.shot import Shot
from app.schemas.shot import ShotCreate, ShotRead

router = APIRouter(tags=["shots"])

WORKSPACE = Path("workspace")
WORKSPACE.mkdir(exist_ok=True)


@router.post("/scenes/{scene_id}/shots", response_model=ShotRead)
async def create_shot(scene_id: UUID, data: ShotCreate, db: AsyncSession = Depends(get_db)):
    shot = Shot(scene_id=scene_id, **data.model_dump())
    db.add(shot)
    await db.commit()
    await db.refresh(shot)
    return shot


@router.get("/scenes/{scene_id}/shots", response_model=list[ShotRead])
async def list_shots(scene_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shot).where(Shot.scene_id == scene_id))
    return result.scalars().all()


@router.post("/shots/{shot_id}/upload-video", response_model=ShotRead)
async def upload_shot_video(shot_id: UUID, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Upload video clip to a shot."""
    result = await db.execute(select(Shot).where(Shot.id == shot_id))
    shot = result.scalar_one_or_none()
    if not shot:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Shot not found")

    # Save file to workspace
    shot_dir = WORKSPACE / "shots"
    shot_dir.mkdir(exist_ok=True)
    file_path = shot_dir / f"{shot_id}{Path(file.filename).suffix}"

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Update shot with video path
    shot.video_path = str(file_path)
    shot.status = "CLIP_ASSIGNED"
    await db.commit()
    await db.refresh(shot)
    return shot


@router.put("/shots/{shot_id}/assign-video")
async def assign_shot_video(shot_id: UUID, data: dict, db: AsyncSession = Depends(get_db)):
    """Assign existing workspace video to a shot."""
    result = await db.execute(select(Shot).where(Shot.id == shot_id))
    shot = result.scalar_one_or_none()
    if not shot:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Shot not found")

    shot.video_path = data.get("video_path")
    shot.status = "CLIP_ASSIGNED" if shot.video_path else "PENDING"
    await db.commit()
    await db.refresh(shot)
    return ShotRead.model_validate(shot)
