# Instrucciones para agentes (always-on)

## Cómo trabajar
- Antes de tocar código: identifica la capa correcta (domain/application/infrastructure/adapters).
- Cambios pequeños e iterativos: un commit lógico por paso (si aplica).
- Evita “big bang refactors”; prioriza extensibilidad.

## Calidad
- Si modificas un parser, añade/actualiza un fixture HTML y un test snapshot.
- Si añades un modelo ORM o relación, añade migración Alembic y test de upsert.
- Si tocas networking, añade test con respuestas mockeadas.

## Validación mínima antes de dar por finalizado
- Ejecuta lint y tests.
- Prueba al menos un flujo CLI: `scrape --portal uvigo --entity publications --limit 20`.

## Preferencias
- Prefiero soluciones simples, legibles y tipadas.
- Evita scraping con navegador (Playwright/Selenium) salvo que sea imprescindible.
- No asumir acceso autenticado; todo debe funcionar en modo público.
