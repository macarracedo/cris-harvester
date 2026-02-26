from __future__ import annotations

from pathlib import Path

from cris_harvester.adapters.uvigo import UVigoAdapter


FIXTURES = Path(__file__).parent / "fixtures" / "uvigo"


def test_uvigo_researchers_list_parser_extracts_urls():
    html = (FIXTURES / "researchers_list.html").read_text(encoding="utf-8")
    adapter = UVigoAdapter()
    urls = adapter.parse_list_page("researchers", html, adapter.seed_endpoints()["researchers"])
    assert urls
    assert any("/investigadores/" in url for url in urls)


def test_uvigo_publications_list_parser_extracts_urls():
    html = (FIXTURES / "publications_list.html").read_text(encoding="utf-8")
    adapter = UVigoAdapter()
    urls = adapter.parse_list_page("publications", html, adapter.seed_endpoints()["publications"])
    assert urls
    assert any("/documentos/" in url for url in urls)


def test_uvigo_researcher_detail_parser_extracts_name_and_orcid():
    html = (FIXTURES / "researchers_detail.html").read_text(encoding="utf-8")
    adapter = UVigoAdapter()
    entity = adapter.parse_entity("researchers", html, "https://portalcientifico.uvigo.gal/investigadores/juan-perez")
    assert entity.name
    assert entity.given_name == "Juan"
    assert entity.family_name == "Pérez"
    assert entity.orcid == "0000-0002-1825-0097"


def test_uvigo_publication_detail_parser_extracts_title_and_year():
    html = (FIXTURES / "publications_detail.html").read_text(encoding="utf-8")
    adapter = UVigoAdapter()
    entity = adapter.parse_entity("publications", html, "https://portalcientifico.uvigo.gal/documentos/699e218f9cb17f04ae69235f")
    assert entity.title == "A Sample Publication Title"
    assert entity.year == 2022
    assert entity.doi == "10.1234/example.doi"
    assert entity.journal_title == "Actualidad civil"
    assert entity.journal_issn == "0213-7100"
    assert entity.publication_date == "2022-05-10"
    assert entity.authors
