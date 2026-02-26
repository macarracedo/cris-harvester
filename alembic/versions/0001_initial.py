"""Initial tables for researchers and publications.

Revision ID: 0001_initial
Revises: 
Create Date: 2026-02-26
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS researcher_publications")
    op.execute("DROP TABLE IF EXISTS researcher_indicators")
    op.execute("DROP TABLE IF EXISTS journal_indicators")
    op.execute("DROP TABLE IF EXISTS publications")
    op.execute("DROP TABLE IF EXISTS researchers")
    op.execute("DROP TABLE IF EXISTS research_groups")
    op.execute("DROP TABLE IF EXISTS areas")
    op.execute("DROP TABLE IF EXISTS campuses")
    op.execute("DROP TABLE IF EXISTS centers")
    op.execute("DROP TABLE IF EXISTS departments")
    op.execute("DROP TABLE IF EXISTS journals")

    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_portal", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source_portal", "name", name="uq_department_source_name"),
    )
    op.create_index("ix_departments_source_portal", "departments", ["source_portal"])

    op.create_table(
        "centers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_portal", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source_portal", "name", name="uq_center_source_name"),
    )
    op.create_index("ix_centers_source_portal", "centers", ["source_portal"])

    op.create_table(
        "campuses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_portal", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source_portal", "name", name="uq_campus_source_name"),
    )
    op.create_index("ix_campuses_source_portal", "campuses", ["source_portal"])

    op.create_table(
        "areas",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_portal", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source_portal", "name", name="uq_area_source_name"),
    )
    op.create_index("ix_areas_source_portal", "areas", ["source_portal"])

    op.create_table(
        "research_groups",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_portal", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source_portal", "name", name="uq_research_group_source_name"),
    )
    op.create_index("ix_research_groups_source_portal", "research_groups", ["source_portal"])

    op.create_table(
        "researchers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_portal", sa.String(length=50), nullable=False),
        sa.Column("url_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("orcid", sa.String(length=64), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("center_id", sa.Integer(), sa.ForeignKey("centers.id"), nullable=True),
        sa.Column("campus_id", sa.Integer(), sa.ForeignKey("campuses.id"), nullable=True),
        sa.Column("area_id", sa.Integer(), sa.ForeignKey("areas.id"), nullable=True),
        sa.Column("research_group_id", sa.Integer(), sa.ForeignKey("research_groups.id"), nullable=True),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source_portal", "url_id", name="uq_researcher_source"),
    )
    op.create_index("ix_researchers_source_portal", "researchers", ["source_portal"])

    op.create_table(
        "journals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_portal", sa.String(length=50), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=False),
        sa.Column("issn", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=True),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source_portal", "issn", name="uq_journal_source"),
    )
    op.create_index("ix_journals_source_portal", "journals", ["source_portal"])

    op.create_table(
        "publications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_portal", sa.String(length=50), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=False),
        sa.Column("document_code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("doi", sa.String(length=200), nullable=True),
        sa.Column("publication_date", sa.String(length=50), nullable=True),
        sa.Column("journal_id", sa.Integer(), sa.ForeignKey("journals.id"), nullable=True),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source_portal", "document_code", name="uq_publication_doc"),
        sa.UniqueConstraint("doi", name="uq_publication_doi"),
    )
    op.create_index("ix_publications_source_portal", "publications", ["source_portal"])
    op.create_index("ix_publications_document_code", "publications", ["document_code"])

    op.create_table(
        "journal_indicators",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("journal_id", sa.Integer(), sa.ForeignKey("journals.id"), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("journal_id", "year", name="uq_journal_indicator"),
    )
    op.create_index("ix_journal_indicators_journal_id", "journal_indicators", ["journal_id"])

    op.create_table(
        "researcher_indicators",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("researcher_id", sa.Integer(), sa.ForeignKey("researchers.id"), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("h_index", sa.Integer(), nullable=True),
        sa.Column("publications_count", sa.Integer(), nullable=True),
        sa.Column("citations_count", sa.Integer(), nullable=True),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("researcher_id", "year", name="uq_researcher_indicator"),
    )
    op.create_index("ix_researcher_indicators_researcher_id", "researcher_indicators", ["researcher_id"])

    op.create_table(
        "researcher_publications",
        sa.Column("researcher_id", sa.Integer(), sa.ForeignKey("researchers.id"), primary_key=True),
        sa.Column("publication_id", sa.Integer(), sa.ForeignKey("publications.id"), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("researcher_publications")
    op.drop_index("ix_researcher_indicators_researcher_id", table_name="researcher_indicators")
    op.drop_table("researcher_indicators")
    op.drop_index("ix_journal_indicators_journal_id", table_name="journal_indicators")
    op.drop_table("journal_indicators")
    op.drop_index("ix_publications_source_portal", table_name="publications")
    op.drop_table("publications")
    op.drop_index("ix_researchers_source_portal", table_name="researchers")
    op.drop_table("researchers")
    op.drop_index("ix_research_groups_source_portal", table_name="research_groups")
    op.drop_table("research_groups")
    op.drop_index("ix_areas_source_portal", table_name="areas")
    op.drop_table("areas")
    op.drop_index("ix_campuses_source_portal", table_name="campuses")
    op.drop_table("campuses")
    op.drop_index("ix_centers_source_portal", table_name="centers")
    op.drop_table("centers")
    op.drop_index("ix_departments_source_portal", table_name="departments")
    op.drop_table("departments")
    op.drop_index("ix_journals_source_portal", table_name="journals")
    op.drop_table("journals")
