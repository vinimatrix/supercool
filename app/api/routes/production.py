from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.scene import Scene
from app.models.shot import Shot
from app.models.shoot import Shoot, ShootStatus

router = APIRouter(prefix="/production", tags=["production"])


# ─── Schemas ────────────────────────────────────────────────────────────────

class SceneCreate(BaseModel):
    project_id: UUID
    scene_number: int
    title: str | None = None
    description: str | None = None
    location: str | None = None
    time_of_day: str | None = None
    mood: str | None = None
    dialogue_script: str | None = None


class SceneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    scene_number: int
    title: str | None = None
    description: str | None = None
    location: str | None = None
    time_of_day: str | None = None
    created_at: datetime


class ShotCreate(BaseModel):
    scene_id: UUID
    shot_number: int
    shot_type: str | None = None
    description: str | None = None
    camera_angle: str | None = None
    camera_movement: str | None = None
    pacing: str | None = None
    duration_seconds: float | None = None
    raw_prompt: str | None = None
    character_ids: list[UUID] | None = None


class ShotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scene_id: UUID
    shot_number: int
    shot_type: str | None = None
    description: str | None = None
    camera_angle: str | None = None
    raw_prompt: str | None = None
    created_at: datetime


class ShootCreate(BaseModel):
    shot_id: UUID
    shoot_number: int
    engine: str | None = None
    seed: int | None = None
    generation_params: dict | None = None


class ShootResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    shot_id: UUID
    shoot_number: int
    status: str
    engine: str | None = None
    clip_score: float | None = None
    qa_status: str | None = None
    qwen_diagnosis: str | None = None
    video_path: str | None = None
    created_at: datetime


class ShootStatusUpdate(BaseModel):
    status: str
    clip_score: float | None = None
    qwen_diagnosis: str | None = None


# ─── Scene Endpoints ────────────────────────────────────────────────────────

@router.post("/scenes", response_model=SceneResponse)
async def create_scene(data: SceneCreate, db: AsyncSession = Depends(get_db)):
    scene = Scene(**data.model_dump())
    db.add(scene)
    await db.commit()
    await db.refresh(scene)
    return scene


@router.get("/scenes/{scene_id}", response_model=SceneResponse)
async def get_scene(scene_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Scene).where(Scene.id == scene_id))
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return scene


@router.get("/scenes", response_model=list[SceneResponse])
async def list_scenes(project_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Scene).where(Scene.project_id == project_id))
    return result.scalars().all()


# ─── Shot Endpoints ─────────────────────────────────────────────────────────

@router.post("/shots", response_model=ShotResponse)
async def create_shot(data: ShotCreate, db: AsyncSession = Depends(get_db)):
    shot = Shot(**data.model_dump())
    db.add(shot)
    await db.commit()
    await db.refresh(shot)
    return shot


@router.get("/shots/{shot_id}", response_model=ShotResponse)
async def get_shot(shot_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shot).where(Shot.id == shot_id))
    shot = result.scalar_one_or_none()
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    return shot


@router.get("/scenes/{scene_id}/shots", response_model=list[ShotResponse])
async def list_shots(scene_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shot).where(Shot.scene_id == scene_id))
    return result.scalars().all()


# ─── Shoot Endpoints ────────────────────────────────────────────────────────

@router.post("/shoots", response_model=ShootResponse)
async def create_shoot(data: ShootCreate, db: AsyncSession = Depends(get_db)):
    shoot = Shoot(**data.model_dump())
    db.add(shoot)
    await db.commit()
    await db.refresh(shoot)
    return shoot


@router.get("/shoots/{shoot_id}", response_model=ShootResponse)
async def get_shoot(shoot_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shoot).where(Shoot.id == shoot_id))
    shoot = result.scalar_one_or_none()
    if not shoot:
        raise HTTPException(status_code=404, detail="Shoot not found")
    return shoot


@router.get("/shots/{shot_id}/shoots", response_model=list[ShootResponse])
async def list_shoots(shot_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shoot).where(Shoot.shot_id == shot_id))
    return result.scalars().all()


@router.patch("/shoots/{shoot_id}/status", response_model=ShootResponse)
async def update_shoot_status(
    shoot_id: UUID, data: ShootStatusUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Shoot).where(Shoot.id == shoot_id))
    shoot = result.scalar_one_or_none()
    if not shoot:
        raise HTTPException(status_code=404, detail="Shoot not found")
    shoot.status = data.status
    if data.clip_score is not None:
        shoot.clip_score = data.clip_score
    if data.qwen_diagnosis is not None:
        shoot.qwen_diagnosis = data.qwen_diagnosis
    await db.commit()
    await db.refresh(shoot)
    return shoot
