from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional, cast

import structlog
import typer

from cris_harvester.adapters.sergas import SergasAdapter
from cris_harvester.adapters.uvigo import UVigoAdapter
from cris_harvester.application.ports import UnitOfWork
from cris_harvester.application.services import crawl_and_persist
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
    Base.metadata.create_all(engine)
    typer.echo(f"Database initialized at {settings.db_url}")


async def _run_scrape(portal: str, entity: str, limit: int) -> None:
    settings = get_settings()
    adapter = get_adapter(portal, settings)
    http_client = AsyncHttpClient(settings)
    uow = SqlAlchemyUnitOfWork(settings.db_url)

    try:
        stats = await crawl_and_persist(adapter, http_client, cast(UnitOfWork, uow), entity, limit)
        typer.echo(
            " | ".join(
                [
                    f"list_pages={stats.list_pages}",
                    f"detail_pages={stats.detail_pages}",
                    f"discovered={stats.discovered}",
                    f"parsed={stats.parsed}",
                    f"persisted={stats.persisted}",
                    f"errors={stats.errors}",
                ]
            )
        )
    finally:
        await http_client.close()


@app.command("scrape")
def scrape(
    portal: str = typer.Option("uvigo", help="Portal adapter"),
    entity: str = typer.Option(..., help="Entity type (researchers, publications)"),
    limit: int = typer.Option(5, help="Limit number of detail pages"),
) -> None:
    asyncio.run(_run_scrape(portal, entity, limit))


if __name__ == "__main__":
    app()
