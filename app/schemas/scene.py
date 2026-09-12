from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class SceneCreate(BaseModel):
    scene_number: int
    title: str | None = None
    location: str | None = None
    time_of_day: str | None = None
    summary: str | None = None


class SceneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    scene_number: int
    title: str | None = None
    location: str | None = None
    time_of_day: str | None = None
    summary: str | None = None
    created_at: datetime
