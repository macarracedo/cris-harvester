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
    entity = adapter.parse_entity("researchers", html, "https://portalcientifico.uvigo.gal/investigadores/277927/detalle")
    assert entity.name
    assert entity.orcid == "0000-0002-1825-0097"
    assert entity.url_id == 277927
    assert entity.email == "juan.perez@uvigo.es"
    assert entity.department_name == "Dereito privado"
    assert entity.center_name == "Facultade de Ciencias Xurídicas e do Traballo"
    assert entity.campus_name == "Vigo"
    assert entity.area_name == "Dereito Civil"
    assert entity.research_group_name == "DL1. Grupo de Dereito Procesual"


def test_uvigo_publication_detail_parser_extracts_title_and_year():
    html = (FIXTURES / "publications_detail.html").read_text(encoding="utf-8")
    adapter = UVigoAdapter()
    entity = adapter.parse_entity("publications", html, "https://portalcientifico.uvigo.gal/documentos/699e218f9cb17f04ae69235f")
    assert entity.title == "A Sample Publication Title"
    assert entity.document_code == "699e218f9cb17f04ae69235f"
    assert entity.year == 2022
    assert entity.doi == "10.1234/example.doi"
    assert entity.journal_title == "Actualidad civil"
    assert entity.journal_issn == "0213-7100"
    assert entity.publication_date == "2022-05-10"
    assert entity.authors
    assert entity.authors[0].url_id == 277927
