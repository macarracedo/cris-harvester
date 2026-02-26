---
applyTo: "**"
---

# Contexto del repositorio
Este repositorio implementa un harvester/scraper modular de portales CRIS (p.ej. UVigo, SERGAS) con adaptadores por portal, parsers por entidad y persistencia relacional con ORM.

# Objetivos de ingeniería (prioridad)
- Modularidad: el core no conoce HTML concreto; todo selector/regla específica va en adapters.
- Mantenibilidad: diseño por capas (domain / application / infrastructure).
- Robustez: rate limiting, retries, timeouts, cache en dev, trazabilidad (raw_html/raw_json opcional).
- Persistencia: SQLAlchemy 2.x + Alembic; upserts; relaciones M:N.
- Tests: unit tests para parsers con fixtures HTML; integración con SQLite in-memory.

# Arquitectura obligatoria
- domain/: modelos (dataclasses o pydantic), normalización, reglas de deduplicación.
- application/: casos de uso (crawl, parse, upsert, export), orquestación.
- infrastructure/: http client, storage ORM, logging, config, CLI.
- adapters/: un adapter por portal (uvigo, sergas, ...).

Patrones esperados:
- Strategy (PortalAdapter por institución)
- Template Method (pipeline de scraping común con hooks)
- Repository + Unit of Work (persistencia transaccional)
- Factory (instanciación de adapters y parsers)

# Estándares de código
- Python 3.12, typing estricto (mypy opcional).
- Formato: ruff + black (o solo ruff si se decide).
- Logging: estructurado; no prints.
- No introducir dependencias nuevas sin justificarlo y sin actualizar pyproject.

# Definición de "Done" para cambios
- Código compila / type-check pasa (si aplica).
- Tests relevantes añadidos/actualizados y pasan.
- Migraciones Alembic creadas/actualizadas si cambian modelos.
- CLI documentada en README si se añaden comandos.
- No romper compatibilidad del core al añadir un nuevo portal.

# Comandos (ajusta cuando existan)
- Instalar: `uv sync` o `pip install -e .[dev]`
- Lint: `ruff check .`
- Tests: `pytest -q`
- Migraciones: `alembic upgrade head`

# Reglas de scraping responsable
- Implementar rate limiting configurable y backoff con jitter.
- Respetar robots.txt cuando `RESPECT_ROBOTS=true`.
- User-Agent configurable y claro.
