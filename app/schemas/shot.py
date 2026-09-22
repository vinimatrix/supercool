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


class ShotUpdate(BaseModel):
    shot_number: int | None = None
    shot_type: str | None = None
    motion_type: str | None = None
    assigned_engine: str | None = None
    prompt_text: str | None = None
    dialogue_text: str | None = None
    speaker_character_id: UUID | None = None
    status: str | None = None


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
    video_path: str | None = None
    speaker_character_id: UUID | None = None
    status: str
    created_at: datetime


class InjectContextRequest(BaseModel):
    custom_prompt: str | None = None
    include_style: bool = True
    ip_adapter_scale: float = 0.85


class InjectContextResponse(BaseModel):
    shot_id: UUID
    original_prompt: str
    injected_prompt: str
    engine: str
    negative_prompt: str


class GenerateRequest(BaseModel):
    scene_id: UUID
    shot_ids: list[UUID] | None = None


class GenerateResponse(BaseModel):
    project_id: UUID | None = None
    scene_id: UUID
    shots_queued: int
    status: str
