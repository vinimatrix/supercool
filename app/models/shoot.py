import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base, get_json_type, get_uuid_type


class ShootStatus(str, Enum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    GENERATED = "GENERATED"
    QA_PENDING = "QA_PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RERENDERING = "RERENDERING"


class Shoot(Base):
    __tablename__ = "shoots"

    id: Mapped[uuid.UUID] = mapped_column(get_uuid_type(), primary_key=True, default=uuid.uuid4)
    shot_id: Mapped[uuid.UUID] = mapped_column(get_uuid_type(), ForeignKey("shots.id", ondelete="CASCADE"))
    shoot_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=ShootStatus.PENDING.value)
    engine: Mapped[str | None] = mapped_column(String(50))
    seed: Mapped[int | None] = mapped_column(Integer)
    generation_params: Mapped[dict | None] = mapped_column(get_json_type())
    video_path: Mapped[str | None] = mapped_column(String(500))
    audio_path: Mapped[str | None] = mapped_column(String(500))
    thumbnail_path: Mapped[str | None] = mapped_column(String(500))
    clip_score: Mapped[float | None] = mapped_column(Float)
    qwen_diagnosis: Mapped[str | None] = mapped_column(Text)
    qa_status: Mapped[str | None] = mapped_column(String(50))
    qa_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    resolution: Mapped[str | None] = mapped_column(String(20))
    fps: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    shot = relationship("Shot", back_populates="shoots")
