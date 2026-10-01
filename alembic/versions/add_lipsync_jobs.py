"""add lipsync_jobs table

Revision ID: d0d0face0001
Revises: c0ffee123abc
Create Date: 2026-09-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d0d0face0001"
down_revision: Union[str, Sequence[str], None] = "c0ffee123abc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lipsync_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="PENDING"),
        sa.Column("stage", sa.String(50), nullable=True),
        sa.Column("video_source", sa.Text(), nullable=False),
        sa.Column("trim_start", sa.Float(), nullable=False),
        sa.Column("trim_end", sa.Float(), nullable=False),
        sa.Column("audio_path", sa.Text(), nullable=False),
        sa.Column("output_path", sa.Text(), nullable=True),
        sa.Column(
            "shot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("shots.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("lipsync_jobs")
