from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.shot import Shot
from app.schemas.shot import ShotCreate, ShotRead

router = APIRouter(tags=["shots"])


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
