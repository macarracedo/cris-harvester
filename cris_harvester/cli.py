from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional, cast

import structlog
import typer

from cris_harvester.adapters.sergas import SergasAdapter
from cris_harvester.adapters.uvigo import UVigoAdapter
from cris_harvester.application.ports import UnitOfWork
from cris_harvester.application.services import crawl_and_persist, update_researcher_indicators
from cris_harvester.config import get_settings
from cris_harvester.infrastructure.db.orm import Base, get_engine
from cris_harvester.infrastructure.db.uow import SqlAlchemyUnitOfWork
from cris_harvester.infrastructure.http import AsyncHttpClient

app = typer.Typer(add_completion=False)
logger = structlog.get_logger(__name__)


def get_adapter(portal: str, settings):
    if portal == "uvigo":
        return UVigoAdapter(publications_list_url=settings.uvigo_publications_list_url)
    if portal == "sergas":
        return SergasAdapter()
    raise typer.BadParameter(f"Unsupported portal: {portal}")


@app.command("init-db")
def init_db() -> None:
    settings = get_settings()
    db_path = settings.db_url.replace("sqlite:///", "")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    engine = get_engine(settings.db_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    typer.echo(f"Database initialized at {settings.db_url}")


async def _run_scrape(
    portal: str,
    entity: str,
    limit: int,
    year_min: Optional[int],
    year_max: Optional[int],
) -> None:
    settings = get_settings()
    adapter = get_adapter(portal, settings)
    http_client = AsyncHttpClient(settings)
    uow = SqlAlchemyUnitOfWork(settings.db_url)

    try:
        stats = await crawl_and_persist(
            adapter,
            http_client,
            cast(UnitOfWork, uow),
            entity,
            limit,
            year_min=year_min,
            year_max=year_max,
        )
        typer.echo(
            " | ".join(
                [
                    f"list_pages={stats.list_pages}",
                    f"detail_pages={stats.detail_pages}",
                    f"discovered={stats.discovered}",
                    f"skipped_existing={stats.skipped_existing}",
                    f"parsed={stats.parsed}",
                    f"persisted={stats.persisted}",
                    f"errors={stats.errors}",
                ]
            )
        )
    finally:
        await http_client.close()


async def _run_researcher_indicators(portal: str, limit: Optional[int]) -> None:
    settings = get_settings()
    adapter = get_adapter(portal, settings)
    http_client = AsyncHttpClient(settings)
    uow = SqlAlchemyUnitOfWork(settings.db_url)
    try:
        count = await update_researcher_indicators(adapter, http_client, cast(UnitOfWork, uow), limit=limit)
        typer.echo(f"researcher_indicators_updated={count}")
    finally:
        await http_client.close()


@app.command("scrape")
def scrape(
    portal: str = typer.Option("uvigo", help="Portal adapter"),
    entity: str = typer.Option(..., help="Entity type (researchers, publications)"),
    limit: int = typer.Option(5, help="Limit number of detail pages"),
    year_min: Optional[int] = typer.Option(None, help="Min publication year filter"),
    year_max: Optional[int] = typer.Option(None, help="Max publication year filter"),
) -> None:
    asyncio.run(_run_scrape(portal, entity, limit, year_min, year_max))


@app.command("update-researcher-indicators")
def update_researcher_indicators_cli(
    portal: str = typer.Option("uvigo", help="Portal adapter"),
    limit: Optional[int] = typer.Option(None, help="Optional limit for researchers to process"),
) -> None:
    asyncio.run(_run_researcher_indicators(portal, limit))


if __name__ == "__main__":
    app()
