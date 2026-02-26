# CRIS Harvester (UVigo / SERGAS / etc.)

Scraper/harvester modular de portales CRIS (Portales Científicos) con adaptadores por institución y persistencia en base de datos relacional mediante SQLAlchemy.

El portal de UVigo expone endpoints públicos para entidades como grupos, investigadores/as, financiación y resultados (publicaciones, tesis, acceso abierto). [source: https://portalcientifico.uvigo.gal/]

## Objetivos
- Arquitectura por capas: domain / application / infrastructure
- Adaptadores intercambiables por portal (Strategy)
- Parsers HTML por entidad (selectolax)
- ORM relacional + migraciones (SQLAlchemy + Alembic)
- Scraping responsable: rate limiting, retries y opción de respetar robots.txt

## Estructura del repo
```
cris-harvester/
├── cris_harvester/
│   ├── adapters/
│   ├── application/
│   ├── domain/
│   ├── infrastructure/
│   └── cli.py
├── alembic/
├── tests/
│   └── fixtures/
├── AGENTS.md
├── alembic.ini
├── cli.py
├── requirements.txt
└── README.md
```

## Instalación (Windows / PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Configuración
Variables de entorno recomendadas (con valores por defecto):
- `CRIS_DB_URL`: `sqlite:///data/cris.db`
- `CRIS_RATE_LIMIT_RPS`: `1.0`
- `CRIS_RESPECT_ROBOTS`: `false` (placeholder; no se aplica robots.txt en el MVP)
- `CRIS_USER_AGENT`: `cris-harvester/0.1 (contact: you@example.com)`
- `CRIS_UVIGO_PUBLICATIONS_LIST_URL`: URL de listado de publicaciones (si quieres forzar un listado anual con parámetros)

## Migraciones
```powershell
alembic upgrade head
```
Nota: en modo pruebas, las migraciones iniciales eliminan y recrean tablas.

## Uso (CLI)
El CLI se implementa con Typer y se puede ejecutar vía módulo.

Inicializar DB (si no usas Alembic todavía):
```powershell
python -m cris_harvester.cli init-db
```
Nota: `init-db` borra y recrea las tablas (modo pruebas).

Scrape con límite pequeño (MVP):
```powershell
python -m cris_harvester.cli scrape --portal uvigo --entity researchers --limit 5
python -m cris_harvester.cli scrape --portal uvigo --entity publications --limit 5
```

Filtros de año (publicaciones):
```powershell
python -m cris_harvester.cli scrape --portal uvigo --entity publications --limit 15 --year-min 2026 --year-max 2026
```

## UI web sencilla
Arranca un panel local para controlar tareas y ver métricas:
```powershell
python -m cris_harvester.web
```
Luego abre `http://127.0.0.1:8000`.

La UI permite:
- Seleccionar portal y entidad.
- Lanzar tareas y detenerlas.
- Ver logs de ejecución.
- Pegar una URL de listado para ajustar filtros (se extraen `min/max`).

## Añadir un portal nuevo
1. Crea `cris_harvester/adapters/<portal>.py` implementando `PortalAdapter`.
2. Implementa `seed_endpoints`, paginación, `parse_list_page` y `parse_entity`.
3. Añade fixtures HTML en `tests/fixtures/<portal>/...` y tests asociados.
4. Ejecuta los tests:
```bash
pytest -q
```

## Entidades mínimas persistidas (MVP)
- Researcher
- Publication