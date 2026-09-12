from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.character import AnchorFace, Character
from app.models.scene import Scene
from app.schemas.character import AnchorFaceCreate, AnchorFaceRead, CharacterCreate, CharacterRead
from app.schemas.scene import SceneCreate, SceneRead

router = APIRouter(tags=["scenes"])


@router.post("/projects/{project_id}/scenes", response_model=SceneRead)
async def create_scene(project_id: UUID, data: SceneCreate, db: AsyncSession = Depends(get_db)):
    scene = Scene(project_id=project_id, **data.model_dump())
    db.add(scene)
    await db.commit()
    await db.refresh(scene)
    return scene


@router.get("/projects/{project_id}/scenes", response_model=list[SceneRead])
async def list_scenes(project_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Scene).where(Scene.project_id == project_id))
    return result.scalars().all()


@router.post("/projects/{project_id}/characters", response_model=CharacterRead)
async def create_character(project_id: UUID, data: CharacterCreate, db: AsyncSession = Depends(get_db)):
    character = Character(project_id=project_id, **data.model_dump())
    db.add(character)
    await db.commit()
    await db.refresh(character)
    return character


@router.post("/characters/{character_id}/anchor-faces", response_model=AnchorFaceRead)
async def create_anchor_face(character_id: UUID, data: AnchorFaceCreate, db: AsyncSession = Depends(get_db)):
    face = AnchorFace(character_id=character_id, **data.model_dump())
    db.add(face)
    await db.commit()
    await db.refresh(face)
    return face
