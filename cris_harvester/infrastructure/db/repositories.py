from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, tuple_, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from cris_harvester.domain.models import (
    Area,
    Campus,
    Center,
    Department,
    Journal,
    JournalIndicator,
    Publication,
    ResearchGroup,
    Researcher,
    ResearcherIndicator,
    ScheduledTask,
)
from cris_harvester.infrastructure.db.orm import (
    AreaORM,
    CampusORM,
    CenterORM,
    DepartmentORM,
    JournalIndicatorORM,
    JournalORM,
    PublicationORM,
    ResearchGroupORM,
    ResearcherIndicatorORM,
    ResearcherORM,
    ScheduledTaskORM,
    researcher_publications,
)


class DepartmentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_many(self, items: list[Department]) -> int:
        if not items:
            return 0
        now = datetime.now(timezone.utc)
        rows = [
            {
                "source_portal": item.source_portal,
                "name": item.name,
                "scraped_at": now,
            }
            for item in items
        ]
        stmt = sqlite_insert(DepartmentORM).values(rows)
        update_cols = {
            "scraped_at": stmt.excluded.scraped_at,
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["source_portal", "name"],
            set_=update_cols,
        )
        result = self._session.execute(stmt)
        return result.rowcount or 0

    def get_ids_by_source_and_name(self, items: list[tuple[str, str]]) -> dict[tuple[str, str], int]:
        if not items:
            return {}
        stmt = (
            select(DepartmentORM.source_portal, DepartmentORM.name, DepartmentORM.id)
            .where(tuple_(DepartmentORM.source_portal, DepartmentORM.name).in_(items))
        )
        result = self._session.execute(stmt).all()
        return {(source_portal, name): item_id for source_portal, name, item_id in result}


class CenterRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_many(self, items: list[Center]) -> int:
        if not items:
            return 0
        now = datetime.now(timezone.utc)
        rows = [
            {
                "source_portal": item.source_portal,
                "name": item.name,
                "scraped_at": now,
            }
            for item in items
        ]
        stmt = sqlite_insert(CenterORM).values(rows)
        update_cols = {
            "scraped_at": stmt.excluded.scraped_at,
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["source_portal", "name"],
            set_=update_cols,
        )
        result = self._session.execute(stmt)
        return result.rowcount or 0

    def get_ids_by_source_and_name(self, items: list[tuple[str, str]]) -> dict[tuple[str, str], int]:
        if not items:
            return {}
        stmt = (
            select(CenterORM.source_portal, CenterORM.name, CenterORM.id)
            .where(tuple_(CenterORM.source_portal, CenterORM.name).in_(items))
        )
        result = self._session.execute(stmt).all()
        return {(source_portal, name): item_id for source_portal, name, item_id in result}


class CampusRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_many(self, items: list[Campus]) -> int:
        if not items:
            return 0
        now = datetime.now(timezone.utc)
        rows = [
            {
                "source_portal": item.source_portal,
                "name": item.name,
                "scraped_at": now,
            }
            for item in items
        ]
        stmt = sqlite_insert(CampusORM).values(rows)
        update_cols = {
            "scraped_at": stmt.excluded.scraped_at,
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["source_portal", "name"],
            set_=update_cols,
        )
        result = self._session.execute(stmt)
        return result.rowcount or 0

    def get_ids_by_source_and_name(self, items: list[tuple[str, str]]) -> dict[tuple[str, str], int]:
        if not items:
            return {}
        stmt = (
            select(CampusORM.source_portal, CampusORM.name, CampusORM.id)
            .where(tuple_(CampusORM.source_portal, CampusORM.name).in_(items))
        )
        result = self._session.execute(stmt).all()
        return {(source_portal, name): item_id for source_portal, name, item_id in result}


class AreaRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_many(self, items: list[Area]) -> int:
        if not items:
            return 0
        now = datetime.now(timezone.utc)
        rows = [
            {
                "source_portal": item.source_portal,
                "name": item.name,
                "scraped_at": now,
            }
            for item in items
        ]
        stmt = sqlite_insert(AreaORM).values(rows)
        update_cols = {
            "scraped_at": stmt.excluded.scraped_at,
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["source_portal", "name"],
            set_=update_cols,
        )
        result = self._session.execute(stmt)
        return result.rowcount or 0

    def get_ids_by_source_and_name(self, items: list[tuple[str, str]]) -> dict[tuple[str, str], int]:
        if not items:
            return {}
        stmt = (
            select(AreaORM.source_portal, AreaORM.name, AreaORM.id)
            .where(tuple_(AreaORM.source_portal, AreaORM.name).in_(items))
        )
        result = self._session.execute(stmt).all()
        return {(source_portal, name): item_id for source_portal, name, item_id in result}


class ResearchGroupRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_many(self, items: list[ResearchGroup]) -> int:
        if not items:
            return 0
        now = datetime.now(timezone.utc)
        rows = [
            {
                "source_portal": item.source_portal,
                "name": item.name,
                "scraped_at": now,
            }
            for item in items
        ]
        stmt = sqlite_insert(ResearchGroupORM).values(rows)
        update_cols = {
            "scraped_at": stmt.excluded.scraped_at,
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["source_portal", "name"],
            set_=update_cols,
        )
        result = self._session.execute(stmt)
        return result.rowcount or 0

    def get_ids_by_source_and_name(self, items: list[tuple[str, str]]) -> dict[tuple[str, str], int]:
        if not items:
            return {}
        stmt = (
            select(ResearchGroupORM.source_portal, ResearchGroupORM.name, ResearchGroupORM.id)
            .where(tuple_(ResearchGroupORM.source_portal, ResearchGroupORM.name).in_(items))
        )
        result = self._session.execute(stmt).all()
        return {(source_portal, name): item_id for source_portal, name, item_id in result}


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
                "url_id": item.url_id,
                "name": item.name,
                "orcid": item.orcid,
                "email": item.email,
                "department_id": item.department_id,
                "center_id": item.center_id,
                "campus_id": item.campus_id,
                "area_id": item.area_id,
                "research_group_id": item.research_group_id,
                "scraped_at": now,
            }
            for item in items
        ]
        stmt = sqlite_insert(ResearcherORM).values(rows)
        update_cols = {
            "name": stmt.excluded.name,
            "orcid": stmt.excluded.orcid,
            "email": stmt.excluded.email,
            "department_id": stmt.excluded.department_id,
            "center_id": stmt.excluded.center_id,
            "campus_id": stmt.excluded.campus_id,
            "area_id": stmt.excluded.area_id,
            "research_group_id": stmt.excluded.research_group_id,
            "scraped_at": stmt.excluded.scraped_at,
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["source_portal", "url_id"],
            set_=update_cols,
        )
        result = self._session.execute(stmt)
        return result.rowcount or 0

    def get_ids_by_url_id(self, url_ids: list[int]) -> dict[int, int]:
        if not url_ids:
            return {}
        stmt = select(ResearcherORM.url_id, ResearcherORM.id).where(ResearcherORM.url_id.in_(url_ids))
        result = self._session.execute(stmt).all()
        return {url_id: researcher_id for url_id, researcher_id in result if url_id is not None}

    def list_url_ids(self) -> list[tuple[int, int]]:
        stmt = select(ResearcherORM.id, ResearcherORM.url_id).where(ResearcherORM.url_id.isnot(None))
        result = self._session.execute(stmt).all()
        return [(researcher_id, url_id) for researcher_id, url_id in result if url_id is not None]


class PublicationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_many(self, items: list[Publication]) -> int:
        if not items:
            return 0
        existing_doi_map = self._get_existing_dois(items)
        now = datetime.now(timezone.utc)
        rows = [
            {
                "source_portal": item.source_portal,
                "source_url": item.source_url,
                "document_code": item.document_code,
                "title": item.title,
                "year": item.year,
                "doi": existing_doi_map.get(item.document_code, item.doi),
                "publication_date": item.publication_date,
                "journal_id": item.journal_id,
                "scraped_at": now,
            }
            for item in items
        ]
        stmt = sqlite_insert(PublicationORM).values(rows)
        update_cols = {
            "document_code": stmt.excluded.document_code,
            "title": stmt.excluded.title,
            "year": stmt.excluded.year,
            "doi": stmt.excluded.doi,
            "publication_date": stmt.excluded.publication_date,
            "journal_id": stmt.excluded.journal_id,
            "scraped_at": stmt.excluded.scraped_at,
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["source_portal", "document_code"],
            set_=update_cols,
        )
        result = self._session.execute(stmt)
        return result.rowcount or 0

    def _get_existing_dois(self, items: list[Publication]) -> dict[str, str | None]:
        dois = [item.doi for item in items if item.doi]
        if not dois:
            return {}
        stmt = select(PublicationORM.doi, PublicationORM.document_code).where(PublicationORM.doi.in_(dois))
        rows = self._session.execute(stmt).all()
        existing = {doi: document_code for doi, document_code in rows if doi}
        doi_map: dict[str, str | None] = {}
        for item in items:
            if not item.doi:
                continue
            existing_code = existing.get(item.doi)
            if existing_code and existing_code != item.document_code:
                doi_map[item.document_code] = None
        return doi_map

    def get_existing_document_codes(self, codes: list[str]) -> set[str]:
        if not codes:
            return set()
        stmt = select(PublicationORM.document_code).where(PublicationORM.document_code.in_(codes))
        result = self._session.execute(stmt).scalars().all()
        return set(result)

    def get_ids_by_document_code(self, codes: list[str]) -> dict[str, int]:
        if not codes:
            return {}
        stmt = select(PublicationORM.document_code, PublicationORM.id).where(PublicationORM.document_code.in_(codes))
        result = self._session.execute(stmt).all()
        return {document_code: publication_id for document_code, publication_id in result}


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
            }
            for item in items
        ]
        stmt = sqlite_insert(JournalORM).values(rows)
        update_cols = {
            "title": stmt.excluded.title,
            "scraped_at": stmt.excluded.scraped_at,
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["source_portal", "issn"],
            set_=update_cols,
        )
        result = self._session.execute(stmt)
        return result.rowcount or 0

    def get_ids_by_issn(self, issn_list: list[str]) -> dict[str, int]:
        if not issn_list:
            return {}
        stmt = select(JournalORM.issn, JournalORM.id).where(JournalORM.issn.in_(issn_list))
        result = self._session.execute(stmt).all()
        return {issn: journal_id for issn, journal_id in result}


class JournalIndicatorRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_many(self, items: list[JournalIndicator]) -> int:
        if not items:
            return 0
        now = datetime.now(timezone.utc)
        rows = [
            {
                "journal_id": item.journal_id,
                "year": item.year,
                "metrics": item.metrics,
                "scraped_at": now,
            }
            for item in items
        ]
        stmt = sqlite_insert(JournalIndicatorORM).values(rows)
        update_cols = {
            "metrics": stmt.excluded.metrics,
            "scraped_at": stmt.excluded.scraped_at,
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["journal_id", "year"],
            set_=update_cols,
        )
        result = self._session.execute(stmt)
        return result.rowcount or 0


class ResearcherPublicationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def insert_many(self, pairs: list[tuple[int, int]]) -> int:
        if not pairs:
            return 0
        rows = [
            {"researcher_id": researcher_id, "publication_id": publication_id}
            for researcher_id, publication_id in pairs
        ]
        stmt = sqlite_insert(researcher_publications).values(rows)
        stmt = stmt.on_conflict_do_nothing(index_elements=["researcher_id", "publication_id"])
        result = self._session.execute(stmt)
        return result.rowcount or 0


class ResearcherIndicatorRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_many(self, items: list[ResearcherIndicator]) -> int:
        if not items:
            return 0
        now = datetime.now(timezone.utc)
        rows = [
            {
                "researcher_id": item.researcher_id,
                "year": item.year,
                "h_index": item.h_index,
                "publications_count": item.publications_count,
                "citations_count": item.citations_count,
                "scraped_at": now,
            }
            for item in items
        ]
        stmt = sqlite_insert(ResearcherIndicatorORM).values(rows)
        update_cols = {
            "h_index": stmt.excluded.h_index,
            "publications_count": stmt.excluded.publications_count,
            "citations_count": stmt.excluded.citations_count,
            "scraped_at": stmt.excluded.scraped_at,
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["researcher_id", "year"],
            set_=update_cols,
        )
        result = self._session.execute(stmt)
        return result.rowcount or 0


class ScheduledTaskRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, task: ScheduledTask) -> int:
        row = ScheduledTaskORM(
            task_type=task.task_type,
            portal=task.portal,
            entity=task.entity,
            limit=task.limit,
            year_min=task.year_min,
            year_max=task.year_max,
            with_researcher_indicators=task.with_researcher_indicators,
            start_at=task.start_at,
            frequency_days=task.frequency_days,
            end_at=task.end_at,
            max_runs=task.max_runs,
            run_count=task.run_count,
            last_run_at=task.last_run_at,
            next_run_at=task.next_run_at,
            status=task.status,
        )
        self._session.add(row)
        self._session.flush()
        return row.id

    def list_all(self) -> list[ScheduledTask]:
        rows = self._session.execute(select(ScheduledTaskORM).order_by(ScheduledTaskORM.id.desc())).scalars().all()
        return [
            ScheduledTask(
                id=row.id,
                task_type=row.task_type,
                portal=row.portal,
                entity=row.entity,
                limit=row.limit,
                year_min=row.year_min,
                year_max=row.year_max,
                with_researcher_indicators=row.with_researcher_indicators,
                start_at=row.start_at,
                frequency_days=row.frequency_days,
                end_at=row.end_at,
                max_runs=row.max_runs,
                run_count=row.run_count,
                last_run_at=row.last_run_at,
                next_run_at=row.next_run_at,
                status=row.status,
            )
            for row in rows
        ]

    def list_due(self, now) -> list[ScheduledTask]:
        stmt = (
            select(ScheduledTaskORM)
            .where(ScheduledTaskORM.status == "active")
            .where(ScheduledTaskORM.next_run_at.isnot(None))
            .where(ScheduledTaskORM.next_run_at <= now)
            .order_by(ScheduledTaskORM.next_run_at)
        )
        rows = self._session.execute(stmt).scalars().all()
        return [
            ScheduledTask(
                id=row.id,
                task_type=row.task_type,
                portal=row.portal,
                entity=row.entity,
                limit=row.limit,
                year_min=row.year_min,
                year_max=row.year_max,
                with_researcher_indicators=row.with_researcher_indicators,
                start_at=row.start_at,
                frequency_days=row.frequency_days,
                end_at=row.end_at,
                max_runs=row.max_runs,
                run_count=row.run_count,
                last_run_at=row.last_run_at,
                next_run_at=row.next_run_at,
                status=row.status,
            )
            for row in rows
        ]

    def mark_run(self, task_id: int, run_count: int, last_run_at, next_run_at) -> None:
        stmt = (
            update(ScheduledTaskORM)
            .where(ScheduledTaskORM.id == task_id)
            .values(run_count=run_count, last_run_at=last_run_at, next_run_at=next_run_at)
        )
        self._session.execute(stmt)

    def update_status(self, task_id: int, status: str) -> None:
        stmt = update(ScheduledTaskORM).where(ScheduledTaskORM.id == task_id).values(status=status)
        self._session.execute(stmt)
