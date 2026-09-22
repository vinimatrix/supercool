from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.character import Character
from app.models.scene import Scene
from app.schemas.character import CharacterCreate, CharacterRead
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
async def create_character(
    project_id: UUID, data: CharacterCreate, db: AsyncSession = Depends(get_db)
):
    character = Character(project_id=project_id, **data.model_dump())
    db.add(character)
    await db.commit()
    await db.refresh(character)
    return character


@router.get("/projects/{project_id}/characters", response_model=list[CharacterRead])
async def list_characters(project_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Character).where(Character.project_id == project_id))
    return result.scalars().all()


@router.delete("/scenes/{scene_id}", status_code=204)
async def delete_scene(scene_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Scene).where(Scene.id == scene_id))
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    await db.delete(scene)
    await db.commit()


@router.delete("/characters/{character_id}", status_code=204)
async def delete_character(character_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    await db.delete(character)
    await db.commit()
