from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import create_engine


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    raw_json: Mapped[dict[str, Any]] = mapped_column(SQLiteJSON, default=dict)


class ResearcherORM(Base, TimestampMixin):
    __tablename__ = "researchers"
    __table_args__ = (UniqueConstraint("source_portal", "source_url", name="uq_researcher_source"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_portal: Mapped[str] = mapped_column(String(50), index=True)
    source_url: Mapped[str] = mapped_column(String(500))
    name: Mapped[str] = mapped_column(String(300))
    given_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    family_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    orcid: Mapped[str | None] = mapped_column(String(64), nullable=True)


class PublicationORM(Base, TimestampMixin):
    __tablename__ = "publications"
    __table_args__ = (UniqueConstraint("source_portal", "source_url", name="uq_publication_source"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_portal: Mapped[str] = mapped_column(String(50), index=True)
    source_url: Mapped[str] = mapped_column(String(500))
    title: Mapped[str] = mapped_column(String(500))
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    doi: Mapped[str | None] = mapped_column(String(200), nullable=True)
    publication_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    journal_title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    journal_issn: Mapped[str | None] = mapped_column(String(32), nullable=True)


class JournalORM(Base, TimestampMixin):
    __tablename__ = "journals"
    __table_args__ = (UniqueConstraint("source_portal", "issn", name="uq_journal_source"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_portal: Mapped[str] = mapped_column(String(50), index=True)
    source_url: Mapped[str] = mapped_column(String(500))
    issn: Mapped[str] = mapped_column(String(32))
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)


class JournalIndicatorORM(Base, TimestampMixin):
    __tablename__ = "journal_indicators"
    __table_args__ = (
        UniqueConstraint("source_portal", "journal_issn", "year", name="uq_journal_indicator"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_portal: Mapped[str] = mapped_column(String(50), index=True)
    source_url: Mapped[str] = mapped_column(String(500))
    journal_issn: Mapped[str] = mapped_column(String(32))
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metrics: Mapped[dict[str, Any]] = mapped_column(SQLiteJSON, default=dict)


def get_engine(db_url: str):
    return create_engine(db_url, future=True)
