import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base, get_json_type, get_uuid_type


class ShotType(str, Enum):
    WIDE = "WIDE"
    MEDIUM = "MEDIUM"
    CLOSE_UP = "CLOSE_UP"
    EXTREME_CLOSE_UP = "EXTREME_CLOSE_UP"
    OVER_SHOULDER = "OVER_SHOULDER"
    POV = "POV"
    AERIAL = "AERIAL"
    TRACKING = "TRACKING"


class Shot(Base):
    __tablename__ = "shots"
    __table_args__ = (UniqueConstraint("scene_id", "shot_number"),)

    id: Mapped[uuid.UUID] = mapped_column(get_uuid_type(), primary_key=True, default=uuid.uuid4)
    scene_id: Mapped[uuid.UUID] = mapped_column(get_uuid_type(), ForeignKey("scenes.id", ondelete="CASCADE"))
    shot_number: Mapped[int] = mapped_column(Integer, nullable=False)
    shot_type: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    camera_angle: Mapped[str | None] = mapped_column(String(50))
    camera_movement: Mapped[str | None] = mapped_column(String(50))
    pacing: Mapped[str | None] = mapped_column(String(50))
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    raw_prompt: Mapped[str | None] = mapped_column(Text)
    injected_prompt: Mapped[str | None] = mapped_column(Text)
    negative_prompt: Mapped[str | None] = mapped_column(Text)
    ip_adapter_weight: Mapped[float | None] = mapped_column(Float)
    character_ids: Mapped[list | None] = mapped_column(get_json_type())
    anchor_face_vectors: Mapped[list | None] = mapped_column(get_json_type())
    motion_type: Mapped[str | None] = mapped_column(String(50))
    assigned_engine: Mapped[str | None] = mapped_column(String(50))
    prompt_text: Mapped[str | None] = mapped_column(Text)
    dialogue_text: Mapped[str | None] = mapped_column(Text)
    video_path: Mapped[str | None] = mapped_column(String(500))
    speaker_character_id: Mapped[uuid.UUID | None] = mapped_column(get_uuid_type(), ForeignKey("characters.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    scene = relationship("Scene", back_populates="shots")
    render_jobs = relationship("RenderJob", back_populates="shot", cascade="all, delete-orphan")
    shoots = relationship("Shoot", back_populates="shot", cascade="all, delete-orphan")
