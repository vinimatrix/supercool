"""initial schema

Revision ID: 8ef5241742e0
Revises: 
Create Date: 2026-09-12 11:59:53.537056

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8ef5241742e0'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('target_resolution', sa.String(20), server_default='4K'),
        sa.Column('fps', sa.Integer, server_default='24'),
        sa.Column('aspect_ratio', sa.String(10), server_default='16:9'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create characters table
    op.create_table(
        'characters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('biography', sa.Text, nullable=True),
        sa.Column('locked_traits', postgresql.JSONB, server_default='[]'),
        sa.Column('voice_profile_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create anchor_faces table
    op.create_table(
        'anchor_faces',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('character_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('characters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('image_url', sa.Text, nullable=False),
        sa.Column('view_angle', sa.String(50), nullable=True),
        sa.Column('is_primary', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create scenes table
    op.create_table(
        'scenes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scene_number', sa.Integer, nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('time_of_day', sa.String(50), nullable=True),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('project_id', 'scene_number', name='uq_scene_project_number'),
    )

    # Create shots table
    op.create_table(
        'shots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('scene_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('scenes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('shot_number', sa.Integer, nullable=False),
        sa.Column('shot_type', sa.String(50), nullable=True),
        sa.Column('motion_type', sa.String(50), nullable=True),
        sa.Column('assigned_engine', sa.String(50), nullable=True),
        sa.Column('prompt_text', sa.Text, nullable=False),
        sa.Column('injected_prompt', sa.Text, nullable=True),
        sa.Column('dialogue_text', sa.Text, nullable=True),
        sa.Column('speaker_character_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('characters.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(50), server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('scene_id', 'shot_number', name='uq_shot_scene_number'),
    )

    # Create render_jobs table
    op.create_table(
        'render_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('shot_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('shots.id', ondelete='CASCADE'), nullable=False),
        sa.Column('engine_name', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), server_default='QUEUED'),
        sa.Column('output_url', sa.Text, nullable=True),
        sa.Column('qa_score', sa.Numeric(4, 3), nullable=True),
        sa.Column('qa_feedback', sa.Text, nullable=True),
        sa.Column('retry_count', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('render_jobs')
    op.drop_table('shots')
    op.drop_table('scenes')
    op.drop_table('anchor_faces')
    op.drop_table('characters')
    op.drop_table('projects')
