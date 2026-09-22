"""Story Bible API - Voice profiles and asset management."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.character import Character

router = APIRouter(prefix="/story-bible", tags=["story-bible"])


class VoiceProfileCreate(BaseModel):
    character_id: UUID
    voice_id: str
    pitch: float | None = None
    language: str = "en"
    lip_sync_weight: float = 1.0


class VoiceProfileRead(BaseModel):
    character_id: UUID
    voice_id: str
    pitch: float | None = None
    language: str
    lip_sync_weight: float


@router.post("/voice-profiles", response_model=VoiceProfileRead)
async def create_voice_profile(data: VoiceProfileCreate, db: AsyncSession = Depends(get_db)):
    """Assign a cloned voice profile to a character."""
    result = await db.execute(select(Character).where(Character.id == data.character_id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    character.voice_profile_id = data.voice_id
    await db.commit()

    return VoiceProfileRead(
        character_id=data.character_id,
        voice_id=data.voice_id,
        pitch=data.pitch,
        language=data.language,
        lip_sync_weight=data.lip_sync_weight,
    )


@router.get("/voice-profiles/{character_id}", response_model=VoiceProfileRead)
async def get_voice_profile(character_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get voice profile for a character."""
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    if not character.voice_profile_id:
        raise HTTPException(status_code=404, detail="No voice profile set for this character")

    return VoiceProfileRead(
        character_id=character.id,
        voice_id=character.voice_profile_id,
        pitch=None,
        language="en",
        lip_sync_weight=1.0,
    )
