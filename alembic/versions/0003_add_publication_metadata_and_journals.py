"""Add publication metadata fields and journal indicator tables.

Revision ID: 0003_add_publication_metadata_and_journals
Revises: 0002_add_researcher_name_parts
Create Date: 2026-02-26
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON

revision = "0003_add_publication_metadata_and_journals"
down_revision = "0002_add_researcher_name_parts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
