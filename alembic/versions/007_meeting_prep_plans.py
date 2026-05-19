"""create meeting_prep_plans table

Revision ID: 007_meeting_prep_plans
Revises: 006_add_analysis_text
Create Date: 2025-01-06 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007_meeting_prep_plans"
down_revision: Union[str, None] = "006_add_analysis_text"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "meeting_prep_plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("company_data", sa.Text(), nullable=False),
        sa.Column("catalog_data", sa.Text(), nullable=False),
        sa.Column("result_markdown", sa.Text(), nullable=False),
        sa.Column("model_used", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("meeting_prep_plans")
