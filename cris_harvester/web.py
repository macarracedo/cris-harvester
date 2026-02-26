from __future__ import annotations

import asyncio
import json
import threading
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast
from urllib.parse import parse_qs, urlparse

import structlog

from cris_harvester.adapters.sergas import SergasAdapter
from cris_harvester.adapters.uvigo import UVigoAdapter
from cris_harvester.application.ports import UnitOfWork
from cris_harvester.application.services import crawl_and_persist, update_researcher_indicators
from cris_harvester.config import get_settings
from sqlalchemy import text

from cris_harvester.domain.models import Publication, Researcher, ScheduledTask
from cris_harvester.infrastructure.db.orm import Base, get_engine
from cris_harvester.infrastructure.db.uow import SqlAlchemyUnitOfWork
from cris_harvester.infrastructure.http import AsyncHttpClient

logger = structlog.get_logger(__name__)

WEB_ROOT = Path(__file__).resolve().parent / "web"

TASKS: dict[str, dict[str, Any]] = {}
TASK_LOCK = threading.Lock()
LOG_LIMIT = 200
SCHEDULER_STOP = threading.Event()


def _log_task(task_id: str, message: str) -> None:
    with TASK_LOCK:
        task = TASKS.get(task_id)
        if task is None:
            return
        logs = task.setdefault("logs", [])
        logs.append(message)
        if len(logs) > LOG_LIMIT:
            del logs[: len(logs) - LOG_LIMIT]


def get_adapter(portal: str, publications_list_url: str | None) -> UVigoAdapter | SergasAdapter:
    if portal == "uvigo":
        return UVigoAdapter(publications_list_url=publications_list_url)
    if portal == "sergas":
        return SergasAdapter()
    raise ValueError(f"Unsupported portal: {portal}")


def build_uvigo_publications_url(year_min: int | None, year_max: int | None) -> str | None:
    if year_min is None and year_max is None:
        return None
    min_value = year_min or year_max
    max_value = year_max or year_min
    return (
        "https://portalcientifico.uvigo.gal/publicaciones?"
        f"agrTipoPublicacion=ARTICLE&min={min_value}&max={max_value}"
    )


def get_db_stats() -> dict[str, int]:
    settings = get_settings()
    engine = get_engine(settings.db_url)
    stats = {
        "departments": 0,
        "centers": 0,
        "campuses": 0,
        "areas": 0,
        "research_groups": 0,
        "researchers": 0,
        "publications": 0,
        "journals": 0,
        "journal_indicators": 0,
        "researcher_publications": 0,
        "researcher_indicators": 0,
    }
    with engine.connect() as conn:
        for table in stats.keys():
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                stats[table] = int(result.scalar() or 0)
            except Exception:  # noqa: BLE001
                stats[table] = 0
    return stats


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _schedule_next_run(task, now: datetime) -> datetime:
    return now + timedelta(days=task.frequency_days)


def _build_task_payload(task: dict[str, Any]) -> dict[str, Any]:
    payload = dict(task)
    for key in ("start_at", "end_at", "last_run_at", "next_run_at"):
        value = payload.get(key)
        if isinstance(value, datetime):
            payload[key] = value.isoformat()
    return payload


def _run_scheduled_task(task_id: str, task: dict[str, Any]) -> None:
    task_type = task.get("task_type")
    portal = task.get("portal") or "uvigo"
    limit = task.get("limit") or 5
    entity = task.get("entity") or "publications"
    year_min = task.get("year_min")
    year_max = task.get("year_max")
    with_researcher_indicators = bool(task.get("with_researcher_indicators"))
    if task_type == "update-researcher-indicators":
        run_researcher_indicator_task(task_id, portal, limit if task.get("limit") else None)
        return
    run_scrape_task(
        task_id,
        portal,
        entity,
        limit,
        year_min,
        year_max,
        None,
        with_researcher_indicators,
    )


def scheduler_loop() -> None:
    settings = get_settings()
    uow = SqlAlchemyUnitOfWork(settings.db_url)
    while not SCHEDULER_STOP.is_set():
        now = datetime.now(timezone.utc)
        with uow:
            due = uow.scheduled_tasks.list_due(now)
            for task in due:
                if task.status != "active" or task.id is None:
                    continue
                if task.end_at and now >= task.end_at:
                    uow.scheduled_tasks.update_status(task.id, "completed")
                    uow.commit()
                    continue
                if task.max_runs is not None and task.run_count >= task.max_runs:
                    uow.scheduled_tasks.update_status(task.id, "completed")
                    uow.commit()
                    continue
                next_run = _schedule_next_run(task, now)
                uow.scheduled_tasks.mark_run(task.id, task.run_count + 1, now, next_run)
                uow.commit()

                task_id = f"task-{len(TASKS) + 1}"
                with TASK_LOCK:
                    TASKS[task_id] = {
                        "status": "running",
                        "portal": task.portal,
                        "entity": task.entity or task.task_type,
                        "limit": task.limit or 0,
                        "year_min": task.year_min,
                        "year_max": task.year_max,
                        "logs": [],
                        "scheduled_task_id": task.id,
                    }
                thread = threading.Thread(
                    target=_run_scheduled_task,
                    args=(
                        task_id,
                        {
                            "task_type": task.task_type,
                            "portal": task.portal,
                            "entity": task.entity,
                            "limit": task.limit,
                            "year_min": task.year_min,
                            "year_max": task.year_max,
                            "with_researcher_indicators": task.with_researcher_indicators,
                        },
                    ),
                    daemon=True,
                )
                thread.start()
        SCHEDULER_STOP.wait(30)


def run_scrape_task(
    task_id: str,
    portal: str,
    entity: str,
    limit: int,
    year_min: int | None,
    year_max: int | None,
    list_url: str | None,
    with_researcher_indicators: bool,
) -> None:
    settings = get_settings()
    publications_list_url = settings.uvigo_publications_list_url
    if portal == "uvigo" and entity == "publications":
        if list_url:
            publications_list_url = list_url
        else:
            publications_list_url = build_uvigo_publications_url(year_min, year_max) or publications_list_url

    adapter = get_adapter(portal, publications_list_url)
    http_client = AsyncHttpClient(settings)
    uow = SqlAlchemyUnitOfWork(settings.db_url)

    def _should_stop() -> bool:
        with TASK_LOCK:
            return TASKS.get(task_id, {}).get("status") == "stopped"

    async def _run() -> None:
        try:
            _log_task(task_id, f"Starting scrape: portal={portal}, entity={entity}, limit={limit}")
            def _on_parsed(item) -> None:
                if entity == "publications" and isinstance(item, Publication):
                    doi_value = item.doi or "-"
                    author_count = len(item.authors)
                    _log_task(
                        task_id,
                        f"publication doi={doi_value} authors={author_count} document_code={item.document_code}",
                    )
                    return
                if entity == "researchers" and isinstance(item, Researcher):
                    name = item.name
                    orcid = item.orcid or "-"
                    _log_task(task_id, f"researcher name={name} orcid={orcid}")
            stats = await crawl_and_persist(
                adapter,
                http_client,
                cast(UnitOfWork, uow),
                entity,
                limit,
                year_min=year_min,
                year_max=year_max,
                should_stop=_should_stop,
                on_parsed=_on_parsed,
                with_researcher_indicators=with_researcher_indicators,
            )
            with TASK_LOCK:
                TASKS[task_id]["status"] = "completed"
                TASKS[task_id]["stats"] = stats.__dict__
            _log_task(
                task_id,
                f"Completed: persisted={stats.persisted}, skipped_existing={stats.skipped_existing}, errors={stats.errors}",
            )
        except Exception as exc:  # noqa: BLE001
            with TASK_LOCK:
                TASKS[task_id]["status"] = "failed"
                TASKS[task_id]["error"] = str(exc)
            _log_task(task_id, f"Failed: {exc}")
        finally:
            await http_client.close()

    asyncio.run(_run())


def run_researcher_indicator_task(
    task_id: str,
    portal: str,
    limit: int | None,
) -> None:
    settings = get_settings()
    adapter = get_adapter(portal, settings.uvigo_publications_list_url)
    http_client = AsyncHttpClient(settings)
    uow = SqlAlchemyUnitOfWork(settings.db_url)

    def _should_stop() -> bool:
        with TASK_LOCK:
            return TASKS.get(task_id, {}).get("status") == "stopped"

    async def _run() -> None:
        try:
            _log_task(task_id, f"Starting researcher indicators: portal={portal}, limit={limit}")
            count = await update_researcher_indicators(
                adapter,
                http_client,
                cast(UnitOfWork, uow),
                limit=limit,
                should_stop=_should_stop,
            )
            with TASK_LOCK:
                TASKS[task_id]["status"] = "completed"
                TASKS[task_id]["stats"] = {"persisted": count}
            _log_task(task_id, f"Completed: persisted={count}")
        except Exception as exc:  # noqa: BLE001
            with TASK_LOCK:
                TASKS[task_id]["status"] = "failed"
                TASKS[task_id]["error"] = str(exc)
            _log_task(task_id, f"Failed: {exc}")
        finally:
            await http_client.close()

    asyncio.run(_run())


class WebHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _serve_file(self, file_path: Path) -> None:
        if not file_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return
        content = file_path.read_bytes()
        content_type = "text/html; charset=utf-8" if file_path.suffix == ".html" else "text/plain"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            return self._serve_file(WEB_ROOT / "index.html")
        if parsed.path == "/api/adapters":
            return self._send_json({"adapters": ["uvigo", "sergas"]})
        if parsed.path == "/api/stats":
            with TASK_LOCK:
                safe_tasks = {
                    task_id: {key: value for key, value in task.items() if key != "thread"}
                    for task_id, task in TASKS.items()
                }
            return self._send_json({"stats": get_db_stats(), "tasks": safe_tasks})
        if parsed.path == "/api/schedules":
            settings = get_settings()
            uow = SqlAlchemyUnitOfWork(settings.db_url)
            with uow:
                schedules = [task.model_dump() for task in uow.scheduled_tasks.list_all()]
            schedules = [_build_task_payload(task) for task in schedules]
            return self._send_json({"schedules": schedules})
        if parsed.path == "/api/logs":
            query = parse_qs(parsed.query)
            task_id = query.get("task_id", [""])[0]
            with TASK_LOCK:
                logs = TASKS.get(task_id, {}).get("logs", [])
            return self._send_json({"task_id": task_id, "logs": logs})
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/init-db":
            settings = get_settings()
            db_path = settings.db_url.replace("sqlite:///", "")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            engine = get_engine(settings.db_url)
            Base.metadata.drop_all(engine)
            Base.metadata.create_all(engine)
            return self._send_json({"status": "ok"})
        if parsed.path == "/api/stop":
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            data = parse_qs(body)
            task_id = data.get("task_id", [""])[0]
            with TASK_LOCK:
                task = TASKS.get(task_id)
                if task and task["status"] == "running":
                    task["status"] = "stopped"
                    _log_task(task_id, "Stop requested")
            return self._send_json({"task_id": task_id, "status": "stopped"})

        if parsed.path == "/api/schedule":
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            data = parse_qs(body)

            task_type = data.get("task_type", ["scrape"])[0]
            portal = data.get("portal", ["uvigo"])[0]
            entity = data.get("entity", [""])[0] or None
            limit_value = data.get("limit", [""])[0]
            limit = int(limit_value) if limit_value else None
            year_min_value = data.get("year_min", [""])[0]
            year_max_value = data.get("year_max", [""])[0]
            year_min = int(year_min_value) if year_min_value else None
            year_max = int(year_max_value) if year_max_value else None
            start_at = _parse_datetime(data.get("start_at", [""])[0])
            frequency_value = data.get("frequency_days", [""])[0]
            frequency_days = int(frequency_value) if frequency_value else 0
            end_at = _parse_datetime(data.get("end_at", [""])[0])
            max_runs_value = data.get("max_runs", [""])[0]
            max_runs = int(max_runs_value) if max_runs_value else None
            with_researcher_indicators_value = data.get("with_researcher_indicators", [""])[0]
            with_researcher_indicators = with_researcher_indicators_value.lower() in {"1", "true", "on", "yes"}

            if start_at is None or frequency_days <= 0:
                return self._send_json({"error": "start_at and frequency_days are required"}, status=400)

            settings = get_settings()
            uow = SqlAlchemyUnitOfWork(settings.db_url)
            with uow:
                task_id = uow.scheduled_tasks.create(
                    ScheduledTask(
                        task_type=task_type,
                        portal=portal,
                        entity=entity,
                        limit=limit,
                        year_min=year_min,
                        year_max=year_max,
                        with_researcher_indicators=with_researcher_indicators,
                        start_at=start_at,
                        frequency_days=frequency_days,
                        end_at=end_at,
                        max_runs=max_runs,
                        run_count=0,
                        last_run_at=None,
                        next_run_at=start_at,
                        status="active",
                    )
                )
                uow.commit()

            return self._send_json({"status": "ok", "id": task_id})

        if parsed.path == "/api/schedule/disable":
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            data = parse_qs(body)
            schedule_id_value = data.get("schedule_id", [""])[0]
            if not schedule_id_value:
                return self._send_json({"error": "schedule_id is required"}, status=400)
            schedule_id = int(schedule_id_value)
            settings = get_settings()
            uow = SqlAlchemyUnitOfWork(settings.db_url)
            with uow:
                uow.scheduled_tasks.update_status(schedule_id, "disabled")
                uow.commit()
            return self._send_json({"status": "disabled", "id": schedule_id})

        if parsed.path == "/api/update-researcher-indicators":
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            data = parse_qs(body)

            portal = data.get("portal", ["uvigo"])[0]
            limit_value = data.get("limit", [""])[0]
            limit = int(limit_value) if limit_value else None

            task_id = f"task-{len(TASKS) + 1}"
            with TASK_LOCK:
                TASKS[task_id] = {
                    "status": "running",
                    "portal": portal,
                    "entity": "researcher_indicators",
                    "limit": limit,
                    "logs": [],
                }

            thread = threading.Thread(
                target=run_researcher_indicator_task,
                args=(task_id, portal, limit),
                daemon=True,
            )
            thread.start()

            return self._send_json({"task_id": task_id, "status": "running"})

        if parsed.path != "/api/scrape":
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        data = parse_qs(body)

        portal = data.get("portal", ["uvigo"])[0]
        entity = data.get("entity", ["publications"])[0]
        limit = int(data.get("limit", ["5"])[0])
        year_min = data.get("year_min", [""])[0]
        year_max = data.get("year_max", [""])[0]
        list_url = data.get("list_url", [""])[0]
        with_researcher_indicators = data.get("with_researcher_indicators", [""])[0]

        year_min_value = int(year_min) if year_min else None
        year_max_value = int(year_max) if year_max else None
        list_url_value = list_url or None
        with_researcher_indicators_value = with_researcher_indicators.lower() in {"1", "true", "on", "yes"}

        task_id = f"task-{len(TASKS) + 1}"
        with TASK_LOCK:
            TASKS[task_id] = {
                "status": "running",
                "portal": portal,
                "entity": entity,
                "limit": limit,
                "year_min": year_min_value,
                "year_max": year_max_value,
                "logs": [],
                "list_url": list_url_value,
                "with_researcher_indicators": with_researcher_indicators_value,
            }

        thread = threading.Thread(
            target=run_scrape_task,
            args=(
                task_id,
                portal,
                entity,
                limit,
                year_min_value,
                year_max_value,
                list_url_value,
                with_researcher_indicators_value,
            ),
            daemon=True,
        )
        thread.start()

        self._send_json({"task_id": task_id, "status": "running"})


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), WebHandler)
    logger.info("web_ui_started", url="http://127.0.0.1:8000")
    scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
    scheduler_thread.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        SCHEDULER_STOP.set()
        server.server_close()


if __name__ == "__main__":
    main()
