---
name: scrape-cli
description: CLI con Typer para ejecutar scraping por portal/entidad y exportar resultados
---

# Comandos requeridos
- `cris-harvester scrape --portal uvigo --entity researchers --limit 50`
- `cris-harvester scrape --portal uvigo --all --limit 50`
- `cris-harvester export --format jsonl --out exports/uvigo_publications.jsonl`

# Reglas
- Mostrar métricas (descubiertas, parseadas, persistidas, errores)
- Config por env vars + opción CLI (DB_URL, RATE_LIMIT, RESPECT_ROBOTS)
