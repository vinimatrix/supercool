from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.character import Character
from app.schemas.character import CharacterRead, CharacterUpdate

router = APIRouter(tags=["characters"])


@router.put("/characters/{character_id}", response_model=CharacterRead)
async def update_character(
    character_id: UUID, data: CharacterUpdate, db: AsyncSession = Depends(get_db)
):
    char = await db.get(Character, character_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    fields = data.model_dump(exclude_unset=True)
    for key, value in fields.items():
        setattr(char, key, value)
    await db.commit()
    await db.refresh(char)
    return char
