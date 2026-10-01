from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MediaItem(BaseModel):
    path: str
    name: str
    size: int
    duration: float | None = None


class LipsyncJobCreate(BaseModel):
    project_id: UUID
    video_path: str
    trim_start: float
    trim_end: float
    audio_path: str
    shot_id: UUID | None = None


class LipsyncAssignRequest(BaseModel):
    shot_id: UUID


class LipsyncJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    status: str
    stage: str | None = None
    video_source: str
    trim_start: float
    trim_end: float
    audio_path: str
    output_path: str | None = None
    shot_id: UUID | None = None
    error: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
