# CRIS Harvester (UVigo / SERGAS / etc.)

Scraper/harvester modular de portales CRIS (Portales Científicos) con adaptadores por institución y persistencia en base de datos relacional mediante SQLAlchemy.

El portal de UVigo expone endpoints públicos para entidades como grupos, investigadores/as, financiación y resultados (publicaciones, tesis, acceso abierto). [source: https://portalcientifico.uvigo.gal/]

## Objetivos
- Arquitectura por capas: domain / application / infrastructure
- Adaptadores intercambiables por portal (Strategy)
- Parsers HTML por entidad (selectolax)
- ORM relacional + migraciones (SQLAlchemy + Alembic)
- Scraping responsable: rate limiting, retries y opción de respetar robots.txt

## Estructura del repo (propuesta)
```
cris-harvester/
├── cris_harvester/
├── domain/
├── application/
├── infrastructure/
├── adapters/
├── tests/
├── fixtures/
├── alembic/
├── .github/
├── copilot-instructions.md
├── .copilot/
├── skills/
├── AGENTS.md
├── requirements.txt
└── README.md
```

## Instalación
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuración
Variables de entorno recomendadas (con valores por defecto):
- `DB_URL`: `sqlite:///data/cris.db`
- `RATE_LIMIT_RPS`: `1.0`
- `RESPECT_ROBOTS`: `true`
- `USER_AGENT`: `cris-harvester/0.1 (contact: you@example.com)`

## Migraciones
```bash
alembic upgrade head
```

## Uso (CLI)
El CLI se implementa con Typer y se expone como `cris-harvester`.

Ejemplos:
```bash
cris-harvester scrape --portal uvigo --entity researchers --limit 50
cris-harvester scrape --portal uvigo --entity publications --limit 200
cris-harvester scrape --portal uvigo --all --limit 50
```

## Añadir un portal nuevo
1. Crea `cris_harvester/adapters/<portal>.py` implementando `PortalAdapter`.
2. Implementa `seed_endpoints`, paginación, `parse_list_page` y `parse_entity`.
3. Añade fixtures HTML en `tests/fixtures/<portal>/...` y tests asociados.
4. Ejecuta los tests:
```bash
pytest -q
```

## Entidades mínimas persistidas
- Researcher
- Group
- Funding (o Project)
- Publication
- Thesis

Relaciones M:N mediante tablas puente.