from __future__ import annotations

from typing import Iterable, Protocol, TypeVar, runtime_checkable

from cris_harvester.domain.models import Journal, JournalIndicator, Publication, Researcher

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


class Repository(Protocol[TEntity]):
    def upsert_many(self, items: list[TEntity]) -> int:
        ...


class UnitOfWork(Protocol):
    @property
    def researchers(self) -> Repository[Researcher]:
        ...

    @property
    def publications(self) -> Repository[Publication]:
        ...

    @property
    def journals(self) -> Repository[Journal]:
        ...

    @property
    def journal_indicators(self) -> Repository[JournalIndicator]:
        ...

    def __enter__(self) -> "UnitOfWork":
        ...

    def __exit__(self, exc_type, exc, tb) -> None:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...
