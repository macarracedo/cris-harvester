"""Add given and family names to researchers.

Revision ID: 0002_add_researcher_name_parts
Revises: 0001_initial
Create Date: 2026-02-26
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_add_researcher_name_parts"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("researchers", sa.Column("given_name", sa.String(length=150), nullable=True))
    op.add_column("researchers", sa.Column("family_name", sa.String(length=200), nullable=True))


def downgrade() -> None:
    op.drop_column("researchers", "family_name")
    op.drop_column("researchers", "given_name")
