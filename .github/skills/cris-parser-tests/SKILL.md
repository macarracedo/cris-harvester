---
name: cris-parser-tests
description: Tests unitarios de parsers con selectolax y fixtures HTML (list y detail)
---

# Estructura
- Fixtures: `tests/fixtures/<portal>/<entity>/{list,detail}/*.html`
- Tests: `tests/test_<portal>_<entity>_parser.py`

# Reglas de asserts
- Assert solo campos estables (nombre/título/año/urls/ids).
- Evitar contadores, textos de UI, o elementos que cambian con frecuencia.
- Añadir al menos 1 fixture de lista y 1 de detalle por entidad.

# Stack test
- pytest
- pytest-asyncio si el parseo depende de funciones async (idealmente los parsers son sync)
