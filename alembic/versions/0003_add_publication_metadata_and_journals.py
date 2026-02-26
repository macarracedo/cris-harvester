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
    op.add_column("publications", sa.Column("doi", sa.String(length=200), nullable=True))
    op.add_column("publications", sa.Column("publication_date", sa.String(length=50), nullable=True))
    op.add_column("publications", sa.Column("journal_title", sa.String(length=300), nullable=True))
    op.add_column("publications", sa.Column("journal_issn", sa.String(length=32), nullable=True))

    op.create_table(
        "journals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_portal", sa.String(length=50), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=False),
        sa.Column("issn", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=True),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_json", SQLiteJSON(), nullable=False),
        sa.UniqueConstraint("source_portal", "issn", name="uq_journal_source"),
    )
    op.create_index("ix_journals_source_portal", "journals", ["source_portal"])

    op.create_table(
        "journal_indicators",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_portal", sa.String(length=50), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=False),
        sa.Column("journal_issn", sa.String(length=32), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("metrics", SQLiteJSON(), nullable=False),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_json", SQLiteJSON(), nullable=False),
        sa.UniqueConstraint("source_portal", "journal_issn", "year", name="uq_journal_indicator"),
    )
    op.create_index("ix_journal_indicators_source_portal", "journal_indicators", ["source_portal"])


def downgrade() -> None:
    op.drop_index("ix_journal_indicators_source_portal", table_name="journal_indicators")
    op.drop_table("journal_indicators")
    op.drop_index("ix_journals_source_portal", table_name="journals")
    op.drop_table("journals")
    op.drop_column("publications", "journal_issn")
    op.drop_column("publications", "journal_title")
    op.drop_column("publications", "publication_date")
    op.drop_column("publications", "doi")
