---
name: orm-migrations
description: Modelos SQLAlchemy 2.x + migraciones Alembic + upsert (Postgres/SQLite)
---

# ORM
- SQLAlchemy 2.x, DeclarativeBase, Mapped[]
- Campos comunes: source_portal, source_url, source_id (nullable), scraped_at, last_seen_at, raw_json

# Unicidad y upsert
- UniqueConstraint(source_portal, source_url)
- Upsert:
  - PostgreSQL: insert().on_conflict_do_update
  - SQLite: fallback merge/upsert por query + update

# Entidades mínimas
- Researcher, Group, Funding, Publication, Thesis
- Tablas puente M:N: researcher_publication, researcher_group, funding_participant

# Migraciones
- Alembic autogenerate + revisión manual
- Test mínimo: crear DB, insertar y repetir (debe actualizar, no duplicar)
