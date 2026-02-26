from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Callable, Sequence, cast

import structlog

from cris_harvester.application.ports import EntityModel, EntityType, PortalAdapter, UnitOfWork
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
from cris_harvester.infrastructure.http import AsyncHttpClient

logger = structlog.get_logger(__name__)


@dataclass
class CrawlStats:
    list_pages: int = 0
    detail_pages: int = 0
    discovered: int = 0
    skipped_existing: int = 0
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
    year_min: int | None = None,
    year_max: int | None = None,
    should_stop: Callable[[], bool] | None = None,
    on_parsed: Callable[[EntityModel], None] | None = None,
    with_researcher_indicators: bool = False,
    on_researcher_persist: Callable[[Researcher], None] | None = None,
    on_researcher_indicator_persist: Callable[[ResearcherIndicator], None] | None = None,
) -> CrawlStats:
    stats = CrawlStats()
    detail_urls: list[str] = []

    list_queue = list(adapter.iter_entity_list_pages(entity_type))
    seen_list_urls: set[str] = set()
    max_list_pages = getattr(adapter, "max_list_pages", None)

    while list_queue:
        if should_stop and should_stop():
            logger.info("crawl_stopped", entity=entity_type)
            break
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

    if entity_type == "publications":
        document_codes: list[str] = []
        url_by_code: dict[str, str] = {}
        for url in detail_urls:
            code = adapter.get_document_code(url)
            if code:
                document_codes.append(code)
                url_by_code[code] = url
        if document_codes:
            with uow:
                existing = uow.publications.get_existing_document_codes(document_codes)
            stats.skipped_existing = len(existing)
            detail_urls = [url for code, url in url_by_code.items() if code not in existing]

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
                on_researcher_persist=on_researcher_persist,
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
            if with_researcher_indicators:
                researcher_url_ids = sorted(
                    {
                        author.url_id
                        for publication in publication_items
                        for author in publication.authors
                        if author.url_id is not None
                    }
                )
                if researcher_url_ids:
                    with uow:
                        id_map = uow.researchers.get_ids_by_url_id(researcher_url_ids)
                    pairs = [(researcher_id, url_id) for url_id, researcher_id in id_map.items()]
                    indicator_count = await update_researcher_indicators_for_pairs(
                        adapter,
                        http_client,
                        uow,
                        pairs,
                        should_stop=should_stop,
                        on_indicator_persist=on_researcher_indicator_persist,
                    )
                    logger.info(
                        "persist_researcher_indicators",
                        entity=entity_type,
                        researcher_indicators=indicator_count,
                    )
        else:
            persisted = persist_batch(
                uow,
                entity_type,
                list(pending),
                on_researcher_persist=on_researcher_persist,
            )
            stats.persisted += persisted
            logger.info("persist_batch", entity=entity_type, persisted=persisted)
        pending.clear()

    for detail_url in detail_urls:
        if should_stop and should_stop():
            logger.info("crawl_stopped", entity=entity_type)
            break
        try:
            html = await http_client.get_text(detail_url)
            stats.detail_pages += 1
            entity = adapter.parse_entity(entity_type, html, detail_url)
            if entity_type == "publications":
                publication = cast(Publication, entity)
                if publication.year is not None:
                    if year_min is not None and publication.year < year_min:
                        continue
                    if year_max is not None and publication.year > year_max:
                        continue
            pending.append(entity)
            stats.parsed += 1
            if on_parsed:
                on_parsed(entity)
            if len(pending) >= batch_size:
                await _flush()
        except Exception as exc:  # noqa: BLE001
            stats.errors += 1
            logger.warning("parse_failed", url=detail_url, error=str(exc))
        await asyncio.sleep(0)

    await _flush()
    return stats


def persist_batch(
    uow: UnitOfWork,
    entity_type: EntityType,
    items: Sequence[EntityModel],
    on_researcher_persist: Callable[[Researcher], None] | None = None,
) -> int:
    if not items:
        return 0

    with uow:
        if entity_type == "researchers":
            researcher_items = cast(list[Researcher], list(items))
            for researcher in researcher_items:
                logger.info(
                    "researcher_persist",
                    name=researcher.name,
                    orcid=researcher.orcid,
                    url_id=researcher.url_id,
                    department=researcher.department_name,
                    source_portal=researcher.source_portal,
                )
                if on_researcher_persist:
                    on_researcher_persist(researcher)
            departments, centers, campuses, areas, groups = _build_lookup_items(researcher_items)
            if departments:
                uow.departments.upsert_many(departments)
            if centers:
                uow.centers.upsert_many(centers)
            if campuses:
                uow.campuses.upsert_many(campuses)
            if areas:
                uow.areas.upsert_many(areas)
            if groups:
                uow.research_groups.upsert_many(groups)

            department_ids = (
                uow.departments.get_ids_by_source_and_name([(item.source_portal, item.name) for item in departments])
                if departments
                else {}
            )
            center_ids = (
                uow.centers.get_ids_by_source_and_name([(item.source_portal, item.name) for item in centers])
                if centers
                else {}
            )
            campus_ids = (
                uow.campuses.get_ids_by_source_and_name([(item.source_portal, item.name) for item in campuses])
                if campuses
                else {}
            )
            area_ids = (
                uow.areas.get_ids_by_source_and_name([(item.source_portal, item.name) for item in areas])
                if areas
                else {}
            )
            group_ids = (
                uow.research_groups.get_ids_by_source_and_name([(item.source_portal, item.name) for item in groups])
                if groups
                else {}
            )
            _assign_lookup_ids(researcher_items, department_ids, center_ids, campus_ids, area_ids, group_ids)
            persisted = uow.researchers.upsert_many(researcher_items)
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
    author_url_ids: set[int] = set()

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
            if author.url_id:
                author_url_ids.add(author.url_id)
            else:
                researchers.append(
                    Researcher(
                        source_portal=publication.source_portal,
                        url_id=None,
                        name=author.name,
                        orcid=author.orcid,
                    )
                )

    semaphore = asyncio.Semaphore(5)

    async def _fetch_researcher(url_id: int) -> Researcher | None:
        async with semaphore:
            try:
                detail_url = adapter.build_researcher_detail_url(url_id)
                html = await http_client.get_text(detail_url)
                return cast(Researcher, adapter.parse_entity("researchers", html, detail_url))
            except Exception as exc:  # noqa: BLE001
                logger.warning("researcher_fetch_failed", url_id=url_id, error=str(exc))
                return None

    if author_url_ids:
        fetched = await asyncio.gather(*[_fetch_researcher(url_id) for url_id in sorted(author_url_ids)])
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


def _build_lookup_items(items: Sequence[Researcher]) -> tuple[list[Department], list[Center], list[Campus], list[Area], list[ResearchGroup]]:
    departments: dict[tuple[str, str], Department] = {}
    centers: dict[tuple[str, str], Center] = {}
    campuses: dict[tuple[str, str], Campus] = {}
    areas: dict[tuple[str, str], Area] = {}
    groups: dict[tuple[str, str], ResearchGroup] = {}

    for researcher in items:
        if researcher.department_name:
            key = (researcher.source_portal, researcher.department_name)
            departments.setdefault(key, Department(source_portal=key[0], name=key[1]))
        if researcher.center_name:
            key = (researcher.source_portal, researcher.center_name)
            centers.setdefault(key, Center(source_portal=key[0], name=key[1]))
        if researcher.campus_name:
            key = (researcher.source_portal, researcher.campus_name)
            campuses.setdefault(key, Campus(source_portal=key[0], name=key[1]))
        if researcher.area_name:
            key = (researcher.source_portal, researcher.area_name)
            areas.setdefault(key, Area(source_portal=key[0], name=key[1]))
        if researcher.research_group_name:
            key = (researcher.source_portal, researcher.research_group_name)
            groups.setdefault(key, ResearchGroup(source_portal=key[0], name=key[1]))

    return list(departments.values()), list(centers.values()), list(campuses.values()), list(areas.values()), list(groups.values())


def _assign_lookup_ids(
    researchers: Sequence[Researcher],
    department_ids: dict[tuple[str, str], int],
    center_ids: dict[tuple[str, str], int],
    campus_ids: dict[tuple[str, str], int],
    area_ids: dict[tuple[str, str], int],
    group_ids: dict[tuple[str, str], int],
) -> None:
    for researcher in researchers:
        if researcher.department_name:
            researcher.department_id = department_ids.get((researcher.source_portal, researcher.department_name))
        if researcher.center_name:
            researcher.center_id = center_ids.get((researcher.source_portal, researcher.center_name))
        if researcher.campus_name:
            researcher.campus_id = campus_ids.get((researcher.source_portal, researcher.campus_name))
        if researcher.area_name:
            researcher.area_id = area_ids.get((researcher.source_portal, researcher.area_name))
        if researcher.research_group_name:
            researcher.research_group_id = group_ids.get((researcher.source_portal, researcher.research_group_name))


def persist_publication_bundle(
    uow: UnitOfWork,
    publications: Sequence[Publication],
    researchers: Sequence[Researcher],
    journals: Sequence[Journal],
    indicators: Sequence[JournalIndicator],
    on_researcher_persist: Callable[[Researcher], None] | None = None,
) -> tuple[int, int, int, int]:
    with uow:
        departments, centers, campuses, areas, groups = _build_lookup_items(researchers)
        if departments:
            uow.departments.upsert_many(departments)
        if centers:
            uow.centers.upsert_many(centers)
        if campuses:
            uow.campuses.upsert_many(campuses)
        if areas:
            uow.areas.upsert_many(areas)
        if groups:
            uow.research_groups.upsert_many(groups)

        department_ids = (
            uow.departments.get_ids_by_source_and_name([(item.source_portal, item.name) for item in departments])
            if departments
            else {}
        )
        center_ids = (
            uow.centers.get_ids_by_source_and_name([(item.source_portal, item.name) for item in centers])
            if centers
            else {}
        )
        campus_ids = (
            uow.campuses.get_ids_by_source_and_name([(item.source_portal, item.name) for item in campuses])
            if campuses
            else {}
        )
        area_ids = (
            uow.areas.get_ids_by_source_and_name([(item.source_portal, item.name) for item in areas])
            if areas
            else {}
        )
        group_ids = (
            uow.research_groups.get_ids_by_source_and_name([(item.source_portal, item.name) for item in groups])
            if groups
            else {}
        )
        _assign_lookup_ids(researchers, department_ids, center_ids, campus_ids, area_ids, group_ids)

        for researcher in researchers:
            logger.info(
                "researcher_persist",
                name=researcher.name,
                orcid=researcher.orcid,
                url_id=researcher.url_id,
                department=researcher.department_name,
                source_portal=researcher.source_portal,
            )
            if on_researcher_persist:
                on_researcher_persist(researcher)

        journal_count = uow.journals.upsert_many(list(journals)) if journals else 0
        issn_map = uow.journals.get_ids_by_issn([journal.issn for journal in journals]) if journals else {}
        for publication in publications:
            if publication.journal_issn and publication.journal_issn in issn_map:
                publication.journal_id = issn_map[publication.journal_issn]
            publication.journal_issn = None
            publication.journal_title = None

        for indicator in indicators:
            if indicator.journal_issn and indicator.journal_issn in issn_map:
                indicator.journal_id = issn_map[indicator.journal_issn]
            indicator.journal_issn = None
        indicators_to_save = [indicator for indicator in indicators if indicator.journal_id]

        pub_count = uow.publications.upsert_many(list(publications)) if publications else 0
        researcher_count = uow.researchers.upsert_many(list(researchers)) if researchers else 0
        indicator_count = uow.journal_indicators.upsert_many(indicators_to_save) if indicators_to_save else 0

        researcher_url_ids = [author.url_id for publication in publications for author in publication.authors if author.url_id]
        researcher_ids = uow.researchers.get_ids_by_url_id([url_id for url_id in researcher_url_ids if url_id is not None])
        publication_ids = uow.publications.get_ids_by_document_code([publication.document_code for publication in publications])
        pairs: list[tuple[int, int]] = []
        for publication in publications:
            publication_id = publication_ids.get(publication.document_code)
            if not publication_id:
                continue
            for author in publication.authors:
                if not author.url_id:
                    continue
                researcher_id = researcher_ids.get(author.url_id)
                if researcher_id:
                    pairs.append((researcher_id, publication_id))
        uow.researcher_publications.insert_many(pairs)

        uow.commit()
        return pub_count, researcher_count, journal_count, indicator_count


async def update_researcher_indicators(
    adapter: PortalAdapter,
    http_client: AsyncHttpClient,
    uow: UnitOfWork,
    limit: int | None = None,
    batch_size: int = 20,
    should_stop: Callable[[], bool] | None = None,
    on_indicator_persist: Callable[[ResearcherIndicator], None] | None = None,
) -> int:
    with uow:
        researcher_pairs = uow.researchers.list_url_ids()

    if limit is not None:
        researcher_pairs = researcher_pairs[:limit]

    indicators: list[ResearcherIndicator] = []
    pending_lock = asyncio.Lock()
    persisted = 0
    semaphore = asyncio.Semaphore(5)

    async def _flush() -> None:
        nonlocal persisted
        if not indicators:
            return
        if on_indicator_persist:
            for indicator in indicators:
                on_indicator_persist(indicator)
        with uow:
            count = uow.researcher_indicators.upsert_many(list(indicators))
            uow.commit()
        persisted += count
        indicators.clear()

    async def _fetch_indicator(researcher_id: int, url_id: int) -> None:
        async with semaphore:
            if should_stop and should_stop():
                return
            urls = adapter.build_researcher_indicator_urls(url_id)
            html_by_key: dict[str, str] = {}

            async def _fetch_url(key: str, indicator_url: str) -> tuple[str, str] | None:
                try:
                    html = await http_client.get_text(indicator_url)
                    return key, html
                except Exception as exc:  # noqa: BLE001
                    logger.warning("indicator_fetch_failed", url=indicator_url, error=str(exc))
                    return None

            results = await asyncio.gather(*[_fetch_url(key, indicator_url) for key, indicator_url in urls.items()])
            for result in results:
                if result:
                    key, html = result
                    html_by_key[key] = html
            if not html_by_key:
                return
            indicator = adapter.parse_researcher_indicators(html_by_key, url_id)
            indicator.researcher_id = researcher_id
            async with pending_lock:
                indicators.append(indicator)
                if len(indicators) >= batch_size:
                    await _flush()

    tasks = [
        _fetch_indicator(researcher_id, url_id)
        for researcher_id, url_id in researcher_pairs
        if not (should_stop and should_stop())
    ]
    if tasks:
        await asyncio.gather(*tasks)

    async with pending_lock:
        await _flush()

    return persisted


async def update_researcher_indicators_for_pairs(
    adapter: PortalAdapter,
    http_client: AsyncHttpClient,
    uow: UnitOfWork,
    researcher_pairs: Sequence[tuple[int, int]],
    batch_size: int = 20,
    should_stop: Callable[[], bool] | None = None,
    on_indicator_persist: Callable[[ResearcherIndicator], None] | None = None,
) -> int:
    if not researcher_pairs:
        return 0

    indicators: list[ResearcherIndicator] = []
    pending_lock = asyncio.Lock()
    persisted = 0
    semaphore = asyncio.Semaphore(5)

    async def _flush() -> None:
        nonlocal persisted
        if not indicators:
            return
        if on_indicator_persist:
            for indicator in indicators:
                on_indicator_persist(indicator)
        with uow:
            count = uow.researcher_indicators.upsert_many(list(indicators))
            uow.commit()
        persisted += count
        indicators.clear()

    async def _fetch_indicator(researcher_id: int, url_id: int) -> None:
        async with semaphore:
            if should_stop and should_stop():
                return
            urls = adapter.build_researcher_indicator_urls(url_id)
            html_by_key: dict[str, str] = {}

            async def _fetch_url(key: str, indicator_url: str) -> tuple[str, str] | None:
                try:
                    html = await http_client.get_text(indicator_url)
                    return key, html
                except Exception as exc:  # noqa: BLE001
                    logger.warning("indicator_fetch_failed", url=indicator_url, error=str(exc))
                    return None

            results = await asyncio.gather(*[_fetch_url(key, indicator_url) for key, indicator_url in urls.items()])
            for result in results:
                if result:
                    key, html = result
                    html_by_key[key] = html
            if not html_by_key:
                return
            indicator = adapter.parse_researcher_indicators(html_by_key, url_id)
            indicator.researcher_id = researcher_id
            async with pending_lock:
                indicators.append(indicator)
                if len(indicators) >= batch_size:
                    await _flush()

    tasks = [
        _fetch_indicator(researcher_id, url_id)
        for researcher_id, url_id in researcher_pairs
        if not (should_stop and should_stop())
    ]
    if tasks:
        await asyncio.gather(*tasks)

    async with pending_lock:
        await _flush()

    return persisted
