from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Sequence, cast

import structlog

from cris_harvester.application.ports import EntityModel, EntityType, PortalAdapter, UnitOfWork
from cris_harvester.domain.models import Journal, JournalIndicator, Publication, Researcher
from cris_harvester.infrastructure.http import AsyncHttpClient

logger = structlog.get_logger(__name__)


@dataclass
class CrawlStats:
    list_pages: int = 0
    detail_pages: int = 0
    discovered: int = 0
    parsed: int = 0
    persisted: int = 0
    errors: int = 0


async def crawl_entity(
    adapter: PortalAdapter,
    http_client: AsyncHttpClient,
    entity_type: EntityType,
    limit: int,
) -> tuple[list[EntityModel], CrawlStats]:
    stats = CrawlStats()
    detail_urls: list[str] = []

    list_queue = list(adapter.iter_entity_list_pages(entity_type))
    seen_list_urls: set[str] = set()
    max_list_pages = getattr(adapter, "max_list_pages", None)

    while list_queue:
        list_url = list_queue.pop(0)
        if list_url in seen_list_urls:
            continue
        seen_list_urls.add(list_url)

        html = await http_client.get_text(list_url)
        stats.list_pages += 1
        urls = adapter.parse_list_page(entity_type, html, list_url)
        for url in urls:
            if url not in detail_urls:
                detail_urls.append(url)
            if 0 < limit <= len(detail_urls):
                break
        if 0 < limit <= len(detail_urls):
            break

        pagination_urls = adapter.parse_list_pagination(entity_type, html, list_url)
        for next_url in pagination_urls:
            if next_url not in seen_list_urls and next_url not in list_queue:
                list_queue.append(next_url)

        if max_list_pages and stats.list_pages >= max_list_pages:
            break
        if not urls and not pagination_urls:
            break

    stats.discovered = len(detail_urls)

    items: list[EntityModel] = []
    for detail_url in detail_urls:
        try:
            html = await http_client.get_text(detail_url)
            stats.detail_pages += 1
            entity = adapter.parse_entity(entity_type, html, detail_url)
            items.append(entity)
            stats.parsed += 1
        except Exception as exc:  # noqa: BLE001
            stats.errors += 1
            logger.warning("parse_failed", url=detail_url, error=str(exc))
        await asyncio.sleep(0)

    return items, stats


async def crawl_and_persist(
    adapter: PortalAdapter,
    http_client: AsyncHttpClient,
    uow: UnitOfWork,
    entity_type: EntityType,
    limit: int,
    batch_size: int = 1,
) -> CrawlStats:
    stats = CrawlStats()
    detail_urls: list[str] = []

    list_queue = list(adapter.iter_entity_list_pages(entity_type))
    seen_list_urls: set[str] = set()
    max_list_pages = getattr(adapter, "max_list_pages", None)

    while list_queue:
        list_url = list_queue.pop(0)
        if list_url in seen_list_urls:
            continue
        seen_list_urls.add(list_url)

        html = await http_client.get_text(list_url)
        stats.list_pages += 1
        urls = adapter.parse_list_page(entity_type, html, list_url)
        for url in urls:
            if url not in detail_urls:
                detail_urls.append(url)
            if 0 < limit <= len(detail_urls):
                break
        if 0 < limit <= len(detail_urls):
            break

        pagination_urls = adapter.parse_list_pagination(entity_type, html, list_url)
        for next_url in pagination_urls:
            if next_url not in seen_list_urls and next_url not in list_queue:
                list_queue.append(next_url)

        if max_list_pages and stats.list_pages >= max_list_pages:
            break
        if not urls and not pagination_urls:
            break

    stats.discovered = len(detail_urls)

    pending: list[EntityModel] = []

    async def _flush() -> None:
        if not pending:
            return
        if entity_type == "publications":
            publication_items = cast(list[Publication], list(pending))
            researchers, journals, indicators = await enrich_publications(
                adapter,
                http_client,
                publication_items,
            )
            pub_count, researcher_count, journal_count, indicator_count = persist_publication_bundle(
                uow,
                publication_items,
                researchers,
                journals,
                indicators,
            )
            stats.persisted += pub_count
            logger.info(
                "persist_batch",
                entity=entity_type,
                publications=pub_count,
                researchers=researcher_count,
                journals=journal_count,
                indicators=indicator_count,
            )
        else:
            persisted = persist_batch(uow, entity_type, list(pending))
            stats.persisted += persisted
            logger.info("persist_batch", entity=entity_type, persisted=persisted)
        pending.clear()

    for detail_url in detail_urls:
        try:
            html = await http_client.get_text(detail_url)
            stats.detail_pages += 1
            entity = adapter.parse_entity(entity_type, html, detail_url)
            pending.append(entity)
            stats.parsed += 1
            if len(pending) >= batch_size:
                await _flush()
        except Exception as exc:  # noqa: BLE001
            stats.errors += 1
            logger.warning("parse_failed", url=detail_url, error=str(exc))
        await asyncio.sleep(0)

    await _flush()
    return stats


def persist_batch(uow: UnitOfWork, entity_type: EntityType, items: Sequence[EntityModel]) -> int:
    if not items:
        return 0

    with uow:
        if entity_type == "researchers":
            persisted = uow.researchers.upsert_many(cast(list[Researcher], list(items)))
        elif entity_type == "publications":
            persisted = uow.publications.upsert_many(cast(list[Publication], list(items)))
        else:
            raise ValueError(f"Unsupported entity type: {entity_type}")
        uow.commit()
        return persisted


async def enrich_publications(
    adapter: PortalAdapter,
    http_client: AsyncHttpClient,
    publications: Sequence[Publication],
) -> tuple[list[Researcher], list[Journal], list[JournalIndicator]]:
    researchers: list[Researcher] = []
    journals: list[Journal] = []
    indicators: list[JournalIndicator] = []

    journal_by_issn: dict[str, Journal] = {}
    author_urls: set[str] = set()

    for publication in publications:
        if publication.journal_issn:
            source_url = publication.indicator_url or publication.source_url
            journal = journal_by_issn.get(publication.journal_issn)
            if journal is None:
                journal = Journal(
                    source_portal=publication.source_portal,
                    source_url=source_url,
                    issn=publication.journal_issn,
                    title=publication.journal_title,
                )
                journal_by_issn[publication.journal_issn] = journal
                journals.append(journal)

        for author in publication.authors:
            if author.source_url:
                author_urls.add(author.source_url)
            else:
                researchers.append(
                    Researcher(
                        source_portal=publication.source_portal,
                        source_url=publication.source_url,
                        name=author.name,
                        given_name=author.given_name,
                        family_name=author.family_name,
                        orcid=author.orcid,
                    )
                )

    semaphore = asyncio.Semaphore(5)

    async def _fetch_researcher(url: str) -> Researcher | None:
        async with semaphore:
            try:
                html = await http_client.get_text(url)
                return cast(Researcher, adapter.parse_entity("researchers", html, url))
            except Exception as exc:  # noqa: BLE001
                logger.warning("researcher_fetch_failed", url=url, error=str(exc))
                return None

    if author_urls:
        fetched = await asyncio.gather(*[_fetch_researcher(url) for url in sorted(author_urls)])
        for item in fetched:
            if item is not None:
                researchers.append(item)

    for publication in publications:
        if publication.indicator_url and publication.journal_issn:
            try:
                html = await http_client.get_text(publication.indicator_url)
                indicator = adapter.parse_journal_indicators(
                    html,
                    publication.indicator_url,
                    publication.journal_issn,
                )
                indicators.append(indicator)
            except Exception as exc:  # noqa: BLE001
                logger.warning("indicator_fetch_failed", url=publication.indicator_url, error=str(exc))

    return researchers, journals, indicators


def persist_publication_bundle(
    uow: UnitOfWork,
    publications: Sequence[Publication],
    researchers: Sequence[Researcher],
    journals: Sequence[Journal],
    indicators: Sequence[JournalIndicator],
) -> tuple[int, int, int, int]:
    with uow:
        pub_count = uow.publications.upsert_many(list(publications)) if publications else 0
        researcher_count = uow.researchers.upsert_many(list(researchers)) if researchers else 0
        journal_count = uow.journals.upsert_many(list(journals)) if journals else 0
        indicator_count = uow.journal_indicators.upsert_many(list(indicators)) if indicators else 0
        uow.commit()
        return pub_count, researcher_count, journal_count, indicator_count
