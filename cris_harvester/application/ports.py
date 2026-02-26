from __future__ import annotations

from typing import Iterable, Protocol, TypeVar, runtime_checkable

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
)

EntityType = str
EntityModel = Researcher | Publication
TEntity = TypeVar("TEntity", bound=EntityModel, contravariant=True)


@runtime_checkable
class PortalAdapter(Protocol):
    portal_name: str

    def seed_endpoints(self) -> dict[str, str]:
        ...

    def iter_entity_list_pages(self, entity_type: EntityType) -> Iterable[str]:
        ...

    def parse_list_page(self, entity_type: EntityType, html: str, url: str) -> list[str]:
        ...

    def parse_list_pagination(self, entity_type: EntityType, html: str, url: str) -> list[str]:
        ...

    def parse_entity(self, entity_type: EntityType, html: str, url: str) -> EntityModel:
        ...

    def parse_journal_indicators(self, html: str, url: str, journal_issn: str) -> JournalIndicator:
        ...

    def get_document_code(self, url: str) -> str | None:
        ...

    def get_researcher_url_id(self, url: str) -> int | None:
        ...

    def build_researcher_detail_url(self, url_id: int) -> str:
        ...

    def build_researcher_indicator_urls(self, url_id: int) -> dict[str, str]:
        ...

    def parse_researcher_indicators(self, html_by_key: dict[str, str], url_id: int) -> ResearcherIndicator:
        ...


class Repository(Protocol[TEntity]):
    def upsert_many(self, items: list[TEntity]) -> int:
        ...


class PublicationRepository(Repository[Publication], Protocol):
    def get_existing_document_codes(self, codes: list[str]) -> set[str]:
        ...

    def get_ids_by_document_code(self, codes: list[str]) -> dict[str, int]:
        ...


class JournalRepository(Repository[Journal], Protocol):
    def get_ids_by_issn(self, issn_list: list[str]) -> dict[str, int]:
        ...


class ResearcherRepository(Repository[Researcher], Protocol):
    def get_ids_by_url_id(self, url_ids: list[int]) -> dict[int, int]:
        ...

    def list_url_ids(self) -> list[tuple[int, int]]:
        ...


class DepartmentRepository(Repository[Department], Protocol):
    def get_ids_by_source_and_name(self, items: list[tuple[str, str]]) -> dict[tuple[str, str], int]:
        ...


class CenterRepository(Repository[Center], Protocol):
    def get_ids_by_source_and_name(self, items: list[tuple[str, str]]) -> dict[tuple[str, str], int]:
        ...


class CampusRepository(Repository[Campus], Protocol):
    def get_ids_by_source_and_name(self, items: list[tuple[str, str]]) -> dict[tuple[str, str], int]:
        ...


class AreaRepository(Repository[Area], Protocol):
    def get_ids_by_source_and_name(self, items: list[tuple[str, str]]) -> dict[tuple[str, str], int]:
        ...


class ResearchGroupRepository(Repository[ResearchGroup], Protocol):
    def get_ids_by_source_and_name(self, items: list[tuple[str, str]]) -> dict[tuple[str, str], int]:
        ...


class ResearcherPublicationRepository(Protocol):
    def insert_many(self, pairs: list[tuple[int, int]]) -> int:
        ...


class ResearcherIndicatorRepository(Repository[ResearcherIndicator], Protocol):
    ...


class UnitOfWork(Protocol):
    @property
    def researchers(self) -> ResearcherRepository:
        ...

    @property
    def departments(self) -> DepartmentRepository:
        ...

    @property
    def centers(self) -> CenterRepository:
        ...

    @property
    def campuses(self) -> CampusRepository:
        ...

    @property
    def areas(self) -> AreaRepository:
        ...

    @property
    def research_groups(self) -> ResearchGroupRepository:
        ...

    @property
    def publications(self) -> PublicationRepository:
        ...

    @property
    def journals(self) -> JournalRepository:
        ...

    @property
    def journal_indicators(self) -> Repository[JournalIndicator]:
        ...

    @property
    def researcher_publications(self) -> ResearcherPublicationRepository:
        ...

    @property
    def researcher_indicators(self) -> ResearcherIndicatorRepository:
        ...

    def __enter__(self) -> "UnitOfWork":
        ...

    def __exit__(self, exc_type, exc, tb) -> None:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...
