from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from cris_harvester.domain.models import Journal, JournalIndicator, Publication, Researcher
from cris_harvester.infrastructure.db.orm import JournalIndicatorORM, JournalORM, PublicationORM, ResearcherORM


class ResearcherRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_many(self, items: list[Researcher]) -> int:
        if not items:
            return 0
        now = datetime.now(timezone.utc)
        rows = [
            {
                "source_portal": item.source_portal,
                "source_url": item.source_url,
                "name": item.name,
                "given_name": item.given_name,
                "family_name": item.family_name,
                "orcid": item.orcid,
                "scraped_at": now,
                "last_seen_at": now,
                "raw_json": item.model_dump(),
            }
            for item in items
        ]
        stmt = sqlite_insert(ResearcherORM).values(rows)
        update_cols = {
            "name": stmt.excluded.name,
            "given_name": stmt.excluded.given_name,
            "family_name": stmt.excluded.family_name,
            "orcid": stmt.excluded.orcid,
            "scraped_at": stmt.excluded.scraped_at,
            "last_seen_at": stmt.excluded.last_seen_at,
            "raw_json": stmt.excluded.raw_json,
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["source_portal", "source_url"],
            set_=update_cols,
        )
        result = self._session.execute(stmt)
        return result.rowcount or 0


class PublicationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_many(self, items: list[Publication]) -> int:
        if not items:
            return 0
        now = datetime.now(timezone.utc)
        rows = [
            {
                "source_portal": item.source_portal,
                "source_url": item.source_url,
                "title": item.title,
                "year": item.year,
                "doi": item.doi,
                "publication_date": item.publication_date,
                "journal_title": item.journal_title,
                "journal_issn": item.journal_issn,
                "scraped_at": now,
                "last_seen_at": now,
                "raw_json": item.model_dump(),
            }
            for item in items
        ]
        stmt = sqlite_insert(PublicationORM).values(rows)
        update_cols = {
            "title": stmt.excluded.title,
            "year": stmt.excluded.year,
            "doi": stmt.excluded.doi,
            "publication_date": stmt.excluded.publication_date,
            "journal_title": stmt.excluded.journal_title,
            "journal_issn": stmt.excluded.journal_issn,
            "scraped_at": stmt.excluded.scraped_at,
            "last_seen_at": stmt.excluded.last_seen_at,
            "raw_json": stmt.excluded.raw_json,
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["source_portal", "source_url"],
            set_=update_cols,
        )
        result = self._session.execute(stmt)
        return result.rowcount or 0


class JournalRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_many(self, items: list[Journal]) -> int:
        if not items:
            return 0
        now = datetime.now(timezone.utc)
        rows = [
            {
                "source_portal": item.source_portal,
                "source_url": item.source_url,
                "issn": item.issn,
                "title": item.title,
                "scraped_at": now,
                "last_seen_at": now,
                "raw_json": item.model_dump(),
            }
            for item in items
        ]
        stmt = sqlite_insert(JournalORM).values(rows)
        update_cols = {
            "title": stmt.excluded.title,
            "scraped_at": stmt.excluded.scraped_at,
            "last_seen_at": stmt.excluded.last_seen_at,
            "raw_json": stmt.excluded.raw_json,
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["source_portal", "issn"],
            set_=update_cols,
        )
        result = self._session.execute(stmt)
        return result.rowcount or 0


class JournalIndicatorRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_many(self, items: list[JournalIndicator]) -> int:
        if not items:
            return 0
        now = datetime.now(timezone.utc)
        rows = [
            {
                "source_portal": item.source_portal,
                "source_url": item.source_url,
                "journal_issn": item.journal_issn,
                "year": item.year,
                "metrics": item.metrics,
                "scraped_at": now,
                "last_seen_at": now,
                "raw_json": item.model_dump(),
            }
            for item in items
        ]
        stmt = sqlite_insert(JournalIndicatorORM).values(rows)
        update_cols = {
            "metrics": stmt.excluded.metrics,
            "scraped_at": stmt.excluded.scraped_at,
            "last_seen_at": stmt.excluded.last_seen_at,
            "raw_json": stmt.excluded.raw_json,
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["source_portal", "journal_issn", "year"],
            set_=update_cols,
        )
        result = self._session.execute(stmt)
        return result.rowcount or 0
