from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class RenderJobCreate(BaseModel):
    engine_name: str


class RenderJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    shot_id: UUID
    engine_name: str
    status: str
    output_url: str | None = None
    qa_score: Decimal | None = None
    qa_feedback: str | None = None
    retry_count: int
    created_at: datetime
    completed_at: datetime | None = None
