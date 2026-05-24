"""create user_settings table

Revision ID: 008_asr_provider_settings
Revises: 007_meeting_prep_plans
Create Date: 2025-01-07 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "008_asr_provider_settings"
down_revision: Union[str, None] = "007_meeting_prep_plans"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_settings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), unique=True, nullable=False, index=True),
        sa.Column("asr_provider", sa.String(100), nullable=False, server_default="mistral"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_settings")
