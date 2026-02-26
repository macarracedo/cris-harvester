from __future__ import annotations

from pathlib import Path

from cris_harvester.adapters.sergas import SergasAdapter


FIXTURES = Path(__file__).parent / "fixtures" / "sergas"


def test_sergas_researchers_list_parser_extracts_urls():
    html = (FIXTURES / "researchers_list.html").read_text(encoding="utf-8")
    adapter = SergasAdapter()
    urls = adapter.parse_list_page("researchers", html, adapter.seed_endpoints()["researchers"])
    assert urls
    assert any("/investigadores/" in url for url in urls)


def test_sergas_publications_list_parser_extracts_urls():
    html = (FIXTURES / "publications_list.html").read_text(encoding="utf-8")
    adapter = SergasAdapter()
    urls = adapter.parse_list_page("publications", html, adapter.seed_endpoints()["publications"])
    assert urls
    assert any("/documentos/" in url or "/publicaciones/" in url for url in urls)


def test_sergas_researcher_detail_parser_extracts_fields():
    html = (FIXTURES / "researchers_detail.html").read_text(encoding="utf-8")
    adapter = SergasAdapter()
    entity = adapter.parse_entity("researchers", html, "https://portalcientifico.sergas.es/investigadores/12345/detalle")
    assert entity.name == "María López"
    assert entity.orcid == "0000-0002-1825-0097"
    assert entity.url_id == 12345
    assert entity.email == "maria.lopez@sergas.es"
    assert entity.department_name == "Medicina Interna"
    assert entity.center_name == "Hospital Clínico"
    assert entity.campus_name == "Santiago"
    assert entity.area_name == "Cardiología"
    assert entity.research_group_name == "BIO-123"


def test_sergas_publication_detail_parser_extracts_fields():
    html = (FIXTURES / "publications_detail.html").read_text(encoding="utf-8")
    adapter = SergasAdapter()
    entity = adapter.parse_entity("publications", html, "https://portalcientifico.sergas.es/documentos/abc123")
    assert entity.title == "Publicación Sergas"
    assert entity.document_code == "abc123"
    assert entity.year == 2023
    assert entity.doi == "10.9999/sergas.doi"
    assert entity.journal_title == "Revista Sergas"
    assert entity.journal_issn == "1234-5678"
    assert entity.publication_date == "2023-04-12"
    assert entity.authors
    assert entity.authors[0].url_id == 12345
