"""Add scheduled tasks table.

Revision ID: 0004_add_scheduled_tasks
Revises: 0003_add_publication_metadata_and_journals
Create Date: 2026-02-26
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0004_add_scheduled_tasks"
down_revision = "0003_add_publication_metadata_and_journals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scheduled_tasks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("task_type", sa.String(length=50), nullable=False),
        sa.Column("portal", sa.String(length=50), nullable=False),
        sa.Column("entity", sa.String(length=50), nullable=True),
        sa.Column("limit", sa.Integer(), nullable=True),
        sa.Column("year_min", sa.Integer(), nullable=True),
        sa.Column("year_max", sa.Integer(), nullable=True),
        sa.Column("with_researcher_indicators", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("frequency_days", sa.Integer(), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_runs", sa.Integer(), nullable=True),
        sa.Column("run_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
    )
    op.create_index("ix_scheduled_tasks_task_type", "scheduled_tasks", ["task_type"], unique=False)
    op.create_index("ix_scheduled_tasks_portal", "scheduled_tasks", ["portal"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_scheduled_tasks_portal", table_name="scheduled_tasks")
    op.drop_index("ix_scheduled_tasks_task_type", table_name="scheduled_tasks")
    op.drop_table("scheduled_tasks")
