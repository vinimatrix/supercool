from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class ShotCreate(BaseModel):
    shot_number: int
    shot_type: str | None = None
    motion_type: str | None = None
    assigned_engine: str | None = None
    prompt_text: str
    dialogue_text: str | None = None
    speaker_character_id: UUID | None = None
    status: str = "PENDING"


class ShotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scene_id: UUID
    shot_number: int
    shot_type: str | None = None
    motion_type: str | None = None
    assigned_engine: str | None = None
    prompt_text: str
    injected_prompt: str | None = None
    dialogue_text: str | None = None
    speaker_character_id: UUID | None = None
    status: str
    created_at: datetime
