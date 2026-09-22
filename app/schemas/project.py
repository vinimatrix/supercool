from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class ProjectCreate(BaseModel):
    title: str
    description: str | None = None
    target_resolution: str = "4K"
    fps: int = 24
    aspect_ratio: str = "16:9"


class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    target_resolution: str | None = None
    fps: int | None = None
    aspect_ratio: str | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None = None
    target_resolution: str
    fps: int
    aspect_ratio: str
    created_at: datetime
    updated_at: datetime
