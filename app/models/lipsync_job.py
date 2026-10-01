import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base, get_uuid_type


class LipsyncJob(Base):
    __tablename__ = "lipsync_jobs"

    id: Mapped[uuid.UUID] = mapped_column(get_uuid_type(), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), ForeignKey("projects.id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    stage: Mapped[str | None] = mapped_column(String(50))
    video_source: Mapped[str] = mapped_column(Text, nullable=False)
    trim_start: Mapped[float] = mapped_column(Float, nullable=False)
    trim_end: Mapped[float] = mapped_column(Float, nullable=False)
    audio_path: Mapped[str] = mapped_column(Text, nullable=False)
    output_path: Mapped[str | None] = mapped_column(Text)
    shot_id: Mapped[uuid.UUID | None] = mapped_column(
        get_uuid_type(), ForeignKey("shots.id", ondelete="SET NULL")
    )
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("status", "PENDING")
        super().__init__(**kwargs)
