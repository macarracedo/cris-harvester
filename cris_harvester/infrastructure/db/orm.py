from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, UniqueConstraint
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import create_engine


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class DepartmentORM(Base, TimestampMixin):
    __tablename__ = "departments"
    __table_args__ = (UniqueConstraint("source_portal", "name", name="uq_department_source_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_portal: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(300))


class CenterORM(Base, TimestampMixin):
    __tablename__ = "centers"
    __table_args__ = (UniqueConstraint("source_portal", "name", name="uq_center_source_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_portal: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(300))


class CampusORM(Base, TimestampMixin):
    __tablename__ = "campuses"
    __table_args__ = (UniqueConstraint("source_portal", "name", name="uq_campus_source_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_portal: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(300))


class AreaORM(Base, TimestampMixin):
    __tablename__ = "areas"
    __table_args__ = (UniqueConstraint("source_portal", "name", name="uq_area_source_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_portal: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(300))


class ResearchGroupORM(Base, TimestampMixin):
    __tablename__ = "research_groups"
    __table_args__ = (UniqueConstraint("source_portal", "name", name="uq_research_group_source_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_portal: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(300))


class ResearcherORM(Base, TimestampMixin):
    __tablename__ = "researchers"
    __table_args__ = (UniqueConstraint("source_portal", "url_id", name="uq_researcher_source"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_portal: Mapped[str] = mapped_column(String(50), index=True)
    url_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(300))
    orcid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    department_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True)
    center_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("centers.id"), nullable=True)
    campus_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("campuses.id"), nullable=True)
    area_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("areas.id"), nullable=True)
    research_group_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("research_groups.id"), nullable=True)


class PublicationORM(Base, TimestampMixin):
    __tablename__ = "publications"
    __table_args__ = (
        UniqueConstraint("source_portal", "document_code", name="uq_publication_doc"),
        UniqueConstraint("doi", name="uq_publication_doi"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_portal: Mapped[str] = mapped_column(String(50), index=True)
    source_url: Mapped[str] = mapped_column(String(500))
    document_code: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(500))
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    doi: Mapped[str | None] = mapped_column(String(200), nullable=True)
    publication_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    journal_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("journals.id"), nullable=True)


class JournalORM(Base, TimestampMixin):
    __tablename__ = "journals"
    __table_args__ = (UniqueConstraint("source_portal", "issn", name="uq_journal_source"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_portal: Mapped[str] = mapped_column(String(50), index=True)
    source_url: Mapped[str] = mapped_column(String(500))
    issn: Mapped[str] = mapped_column(String(32))
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)


researcher_publications = Table(
    "researcher_publications",
    Base.metadata,
    Column("researcher_id", ForeignKey("researchers.id"), primary_key=True),
    Column("publication_id", ForeignKey("publications.id"), primary_key=True),
)


class JournalIndicatorORM(Base, TimestampMixin):
    __tablename__ = "journal_indicators"
    __table_args__ = (UniqueConstraint("journal_id", "year", name="uq_journal_indicator"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    journal_id: Mapped[int] = mapped_column(Integer, ForeignKey("journals.id"))
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metrics: Mapped[dict[str, Any]] = mapped_column(SQLiteJSON, default=dict)


class ResearcherIndicatorORM(Base, TimestampMixin):
    __tablename__ = "researcher_indicators"
    __table_args__ = (UniqueConstraint("researcher_id", "year", name="uq_researcher_indicator"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    researcher_id: Mapped[int] = mapped_column(Integer, ForeignKey("researchers.id"))
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    h_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    publications_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    citations_count: Mapped[int | None] = mapped_column(Integer, nullable=True)


class ScheduledTaskORM(Base):
    __tablename__ = "scheduled_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_type: Mapped[str] = mapped_column(String(50), index=True)
    portal: Mapped[str] = mapped_column(String(50), index=True)
    entity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    with_researcher_indicators: Mapped[bool] = mapped_column(Boolean, default=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    frequency_days: Mapped[int] = mapped_column(Integer)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    max_runs: Mapped[int | None] = mapped_column(Integer, nullable=True)
    run_count: Mapped[int] = mapped_column(Integer, default=0)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")


def get_engine(db_url: str):
    return create_engine(db_url, future=True)
