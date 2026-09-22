from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class CharacterCreate(BaseModel):
    name: str
    biography: str | None = None
    locked_traits: list[str] = []
    voice_profile_id: str | None = None
    visual_prompt: str | None = None


class CharacterUpdate(BaseModel):
    name: str | None = None
    biography: str | None = None
    locked_traits: list[str] | None = None
    visual_prompt: str | None = None


class CharacterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    name: str
    biography: str | None = None
    locked_traits: list[str] = []
    voice_profile_id: str | None = None
    created_at: datetime
    visual_prompt: str | None = None
    reference_sheet_url: str | None = None


class AnchorFaceCreate(BaseModel):
    image_url: str
    view_angle: str | None = None
    is_primary: bool = False


class AnchorFaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    character_id: UUID
    image_url: str
    view_angle: str | None = None
    is_primary: bool
    created_at: datetime
