"""add character reference_sheet_url and visual_prompt

Revision ID: c0ffee123abc
Revises: fcae66ea5e4b
Create Date: 2026-09-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c0ffee123abc"
down_revision: Union[str, Sequence[str], None] = "fcae66ea5e4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("characters", sa.Column("reference_sheet_url", sa.Text(), nullable=True))
    op.add_column("characters", sa.Column("visual_prompt", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("characters", "visual_prompt")
    op.drop_column("characters", "reference_sheet_url")
