"""Initial tables for researchers and publications.

Revision ID: 0001_initial
Revises: 
Create Date: 2026-02-26
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "researchers" not in existing_tables:
        op.create_table(
            "researchers",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("source_portal", sa.String(length=50), nullable=False),
            sa.Column("source_url", sa.String(length=500), nullable=False),
            sa.Column("name", sa.String(length=300), nullable=False),
            sa.Column("orcid", sa.String(length=64), nullable=True),
            sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("raw_json", SQLiteJSON(), nullable=False),
            sa.UniqueConstraint("source_portal", "source_url", name="uq_researcher_source"),
        )
        op.create_index("ix_researchers_source_portal", "researchers", ["source_portal"])

    if "publications" not in existing_tables:
        op.create_table(
            "publications",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("source_portal", sa.String(length=50), nullable=False),
            sa.Column("source_url", sa.String(length=500), nullable=False),
            sa.Column("title", sa.String(length=500), nullable=False),
            sa.Column("year", sa.Integer(), nullable=True),
            sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("raw_json", SQLiteJSON(), nullable=False),
            sa.UniqueConstraint("source_portal", "source_url", name="uq_publication_source"),
        )
        op.create_index("ix_publications_source_portal", "publications", ["source_portal"])


def downgrade() -> None:
    op.drop_index("ix_publications_source_portal", table_name="publications")
    op.drop_table("publications")
    op.drop_index("ix_researchers_source_portal", table_name="researchers")
    op.drop_table("researchers")
