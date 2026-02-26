from __future__ import annotations

from typing import Iterable

from cris_harvester.application.ports import EntityType, PortalAdapter


class SergasAdapter(PortalAdapter):
    portal_name = "sergas"

    def seed_endpoints(self) -> dict[str, str]:
        return {}

    def iter_entity_list_pages(self, entity_type: EntityType) -> Iterable[str]:
        raise NotImplementedError("SERGAS adapter is a stub in this MVP")

    def parse_list_page(self, entity_type: EntityType, html: str, url: str) -> list[str]:
        raise NotImplementedError("SERGAS adapter is a stub in this MVP")

    def parse_list_pagination(self, entity_type: EntityType, html: str, url: str) -> list[str]:
        raise NotImplementedError("SERGAS adapter is a stub in this MVP")

    def parse_entity(self, entity_type: EntityType, html: str, url: str):
        raise NotImplementedError("SERGAS adapter is a stub in this MVP")

    def parse_journal_indicators(self, html: str, url: str, journal_issn: str):
        raise NotImplementedError("SERGAS adapter is a stub in this MVP")
