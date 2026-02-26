---
name: cris-adapter
description: Crear/actualizar un PortalAdapter asíncrono para un portal CRIS (seed URLs, paginación, parsers selectolax)
---

# Objetivo
Añadir soporte a un nuevo portal sin modificar el core.

# Stack obligatorio
- httpx.AsyncClient para HTTP
- selectolax.lexbor.LexborHTMLParser para parseo HTML
- pydantic para modelos de dominio y normalización

# Pasos
1) Crear `cris_harvester/adapters/<portal>.py` con `<Portal>Adapter(PortalAdapter)`.
2) Implementar:
   - `seed_endpoints() -> dict[str,str]`
   - `iter_entity_list_pages(entity_type)` (paginación)
   - `parse_list_page(entity_type, html, url) -> list[str]`
   - `parse_entity(entity_type, html, url) -> DomainModel`
3) Asegurar URLs absolutas (urljoin con base_url).
4) Normalizar texto (strip, espacios múltiples) y fechas.
5) Añadir tests con fixtures HTML.

# Reglas
- Selectores CSS/XPath solo en adapters/parsers.
- Core no debe importar selectolax directamente (solo a través de adapters).
- Guardar siempre source_portal y source_url.
