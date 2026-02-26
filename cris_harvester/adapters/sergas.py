from __future__ import annotations

import re
from typing import Iterable
from urllib.parse import urljoin, urlparse

from selectolax.lexbor import LexborHTMLParser

from cris_harvester.application.ports import EntityType, PortalAdapter
from cris_harvester.domain.models import AuthorRef, JournalIndicator, Publication, Researcher, ResearcherIndicator
from cris_harvester.infrastructure.parsing import normalize_doi, normalize_space, select_first_text, to_abs_url


class SergasAdapter(PortalAdapter):
    portal_name = "sergas"
    base_url = "https://portalcientifico.sergas.es"
    max_list_pages = 25

    def _collect_candidate_links(self, parser: LexborHTMLParser) -> list[str]:
        hrefs: list[str] = []
        for node in parser.css("a"):
            href = node.attributes.get("href")
            if href:
                hrefs.append(href)

        for attr in ("data-href", "data-url"):
            for node in parser.css(f"[{attr}]"):
                value = node.attributes.get(attr)
                if value:
                    hrefs.append(value)
        return hrefs

    def _is_portal_url(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.netloc.endswith(urlparse(self.base_url).netloc)

    def _is_document_detail(self, url: str) -> bool:
        parsed = urlparse(url)
        if not parsed.path.startswith("/documentos"):
            return False
        parts = [part for part in parsed.path.split("/") if part]
        return len(parts) >= 2

    def get_document_code(self, url: str) -> str | None:
        parsed = urlparse(url)
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 2 and parts[0] == "documentos":
            return parts[1]
        return None

    def get_researcher_url_id(self, url: str) -> int | None:
        parsed = urlparse(url)
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 2 and parts[0] == "investigadores":
            try:
                return int(parts[1])
            except ValueError:
                return None
        return None

    def build_researcher_detail_url(self, url_id: int) -> str:
        return f"{self.base_url}/investigadores/{url_id}/detalle"

    def build_researcher_indicator_urls(self, url_id: int) -> dict[str, str]:
        return {
            "impacto": f"{self.base_url}/indicadores/impacto?persona={url_id}",
            "otros": f"{self.base_url}/indicadores/otros?persona={url_id}",
        }

    def _extract_label_value(self, parser: LexborHTMLParser, labels: list[str]) -> str:
        for node in parser.css("li, p, div, span"):
            text = normalize_space(node.text())
            for label in labels:
                if text.lower().startswith(label.lower()):
                    value = normalize_space(text[len(label) :])
                    if value:
                        return value
                    next_node = node.next
                    if next_node is not None:
                        return normalize_space(next_node.text())
        return ""

    def seed_endpoints(self) -> dict[str, str]:
        return {
            "groups": f"{self.base_url}/grupos",
            "researchers": f"{self.base_url}/investigadores/buscar?termino=",
            "fundings": f"{self.base_url}/financiaciones",
            "publications": f"{self.base_url}/resultados/publicaciones",
            "thesis": f"{self.base_url}/resultados/tesis/anualidades",
            "open_access": f"{self.base_url}/resultados/acceso_abierto",
        }

    def iter_entity_list_pages(self, entity_type: EntityType) -> Iterable[str]:
        seeds = self.seed_endpoints()
        if entity_type not in seeds:
            raise ValueError(f"Unsupported entity type: {entity_type}")
        seed_url = seeds[entity_type]
        if entity_type == "researchers":
            for page in range(1, self.max_list_pages + 1):
                separator = "&" if "?" in seed_url else "?"
                yield f"{seed_url}{separator}page={page}"
            return
        if entity_type == "publications":
            for page in range(1, self.max_list_pages + 1):
                separator = "&" if "?" in seed_url else "?"
                yield f"{seed_url}{separator}page={page}"
            return
        yield seed_url

    def parse_list_page(self, entity_type: EntityType, html: str, url: str) -> list[str]:
        parser = LexborHTMLParser(html)
        raw_hrefs = self._collect_candidate_links(parser)
        hrefs = [to_abs_url(self.base_url, href) for href in raw_hrefs]

        if entity_type == "researchers":
            pattern = re.compile(r"/investigadores/(?!buscar)([^/?#]+)", re.IGNORECASE)
        elif entity_type == "publications":
            pattern = re.compile(r"/(documentos|resultados/publicaciones)/([^/?#]+)", re.IGNORECASE)
        else:
            pattern = re.compile(r"$a")

        results: list[str] = []
        for href in hrefs:
            if "/sso/login" in href:
                continue
            if not self._is_portal_url(href):
                continue
            if pattern.search(href):
                if href not in results:
                    results.append(href)
        return results

    def parse_list_pagination(self, entity_type: EntityType, html: str, url: str) -> list[str]:
        parser = LexborHTMLParser(html)
        candidates: list[str] = []

        for node in parser.css("a[rel='next']"):
            href = node.attributes.get("href")
            if href:
                candidates.append(href)

        for node in parser.css("nav.pagination a, .pagination a, ul.pagination a, li.next a, a.next"):
            href = node.attributes.get("href")
            if href:
                candidates.append(href)

        raw_hrefs = candidates + self._collect_candidate_links(parser)
        list_urls: list[str] = []
        for href in raw_hrefs:
            if not href or href.startswith("#"):
                continue
            abs_url = urljoin(url, href)
            if abs_url == url:
                continue
            if "/sso/login" in abs_url:
                continue
            if not self._is_portal_url(abs_url):
                continue
            if entity_type == "researchers":
                if "/investigadores/buscar" not in abs_url:
                    continue
            elif entity_type == "publications":
                if self._is_document_detail(abs_url):
                    continue
                if "/resultados/publicaciones" not in abs_url and "/publicaciones" not in abs_url and "/documentos" not in abs_url:
                    continue
            else:
                continue
            if abs_url not in list_urls:
                list_urls.append(abs_url)

        return list_urls

    def parse_entity(self, entity_type: EntityType, html: str, url: str):
        parser = LexborHTMLParser(html)

        if entity_type == "researchers":
            name = select_first_text(
                parser,
                ["h1", "h1.title", "h1.page-title", ".profile-header h1", ".name"],
            )
            orcid = ""
            for node in parser.css("a"):
                href = node.attributes.get("href")
                if href and "orcid.org" in href:
                    orcid = href.split("orcid.org/")[-1]
                    break
            email = ""
            mail_node = parser.css_first("a[href^='mailto:']")
            if mail_node:
                mail_href = mail_node.attributes.get("href")
                if mail_href and "mailto:" in mail_href:
                    email = mail_href.replace("mailto:", "")
            if not email:
                email = self._extract_label_value(parser, ["Correo:", "E-mail:", "Email:"])

            department_name = self._extract_label_value(parser, ["Departamento:"])
            center_name = self._extract_label_value(parser, ["Centro:"])
            campus_name = self._extract_label_value(parser, ["Campus:"])
            area_name = self._extract_label_value(parser, ["Área:", "Area:"])
            group_name = self._extract_label_value(
                parser,
                ["Grupo de investigación:", "Grupo de investigacion:", "Grupo de investigación", "Grupo de investigacion"],
            )
            name = normalize_space(name or "") or "Unknown"
            return Researcher(
                source_portal=self.portal_name,
                url_id=self.get_researcher_url_id(url),
                name=name,
                orcid=orcid or None,
                email=normalize_space(email) or None,
                department_name=department_name or None,
                center_name=center_name or None,
                campus_name=campus_name or None,
                area_name=area_name or None,
                research_group_name=group_name or None,
            )

        if entity_type == "publications":
            title = select_first_text(
                parser,
                ["h1", "h1.title", "h1.page-title", ".publication-title"],
            )
            if not title:
                meta_title = parser.css_first("meta[name='citation_title']")
                if meta_title:
                    title = meta_title.attributes.get("content", "")
            year = None
            meta_date = parser.css_first("meta[name='citation_publication_date']")
            if meta_date:
                date_value = meta_date.attributes.get("content") or ""
                match = re.search(r"(19|20)\d{2}", date_value)
                if match:
                    year = int(match.group(0))
            if year is None:
                text = normalize_space(parser.text())
                match = re.search(r"(19|20)\d{2}", text)
                if match:
                    year = int(match.group(0))
            doi = ""
            for node in parser.css("a"):
                href = node.attributes.get("href")
                if href and "doi.org" in href:
                    doi = href.split("doi.org/")[-1]
                    break
            if not doi:
                doi_text = self._extract_label_value(parser, ["DOI:", "Doi:", "doi:"])
                doi = doi_text

            journal_title = self._extract_label_value(parser, ["Revista:", "Journal:", "Xornal:"])
            journal_issn = self._extract_label_value(parser, ["ISSN:", "Issn:", "issn:"])
            publication_date = self._extract_label_value(
                parser,
                ["Data de publicación:", "Fecha de publicación:", "Data de publicacion:", "Publication date:"],
            )

            indicator_url = ""
            for node in parser.css("a"):
                href = node.attributes.get("href")
                if href and "/indicadores/revistas/" in href:
                    indicator_url = to_abs_url(self.base_url, href)
                    break

            authors: list[AuthorRef] = []
            for node in parser.css("a"):
                href = node.attributes.get("href")
                if href and "/investigadores/" in href:
                    author_name = normalize_space(node.text())
                    url_id = self.get_researcher_url_id(href)
                    authors.append(
                        AuthorRef(
                            name=author_name or "Unknown",
                            url_id=url_id,
                        )
                    )
            title = normalize_space(title or "") or "Untitled"
            document_code = self.get_document_code(url)
            if not document_code:
                raise ValueError("Missing document code in URL")
            return Publication(
                source_portal=self.portal_name,
                source_url=url,
                document_code=document_code,
                title=title,
                year=year,
                doi=normalize_doi(doi) or None,
                publication_date=publication_date or None,
                journal_title=journal_title or None,
                journal_issn=journal_issn or None,
                indicator_url=indicator_url or None,
                authors=authors,
            )

        raise ValueError(f"Unsupported entity type: {entity_type}")

    def parse_journal_indicators(self, html: str, url: str, journal_issn: str) -> JournalIndicator:
        parser = LexborHTMLParser(html)
        metrics: dict[str, str] = {}

        for row in parser.css("table tr"):
            cells = row.css("td")
            if len(cells) >= 2:
                key = normalize_space(cells[0].text())
                value = normalize_space(cells[1].text())
                if key and value:
                    metrics[key] = value

        if not metrics:
            for node in parser.css("li, p, div"):
                text = normalize_space(node.text())
                if ":" in text:
                    key, value = [part.strip() for part in text.split(":", maxsplit=1)]
                    if key and value:
                        metrics[key] = value

        year = None
        text = normalize_space(parser.text())
        match = re.search(r"(19|20)\d{2}", text)
        if match:
            year = int(match.group(0))

        return JournalIndicator(
            journal_issn=journal_issn,
            year=year,
            metrics=metrics,
        )

    def parse_researcher_indicators(self, html_by_key: dict[str, str], url_id: int) -> ResearcherIndicator:
        h_index = None
        citations = None
        publications = None

        other_html = html_by_key.get("otros")
        if other_html:
            parser = LexborHTMLParser(other_html)
            text = normalize_space(parser.text()).lower()
            h_match = re.search(r"h-index\s*[:\-]?\s*(\d+)", text)
            if h_match:
                h_index = int(h_match.group(1))
            cit_match = re.search(r"citas[^\d]*(\d+)", text)
            if cit_match:
                citations = int(cit_match.group(1))

        impact_html = html_by_key.get("impacto")
        if impact_html:
            parser = LexborHTMLParser(impact_html)
            text = normalize_space(parser.text()).lower()
            counts = [int(value) for value in re.findall(r"(\d+)\s+(?:publicaci[óo]ns|artigos)", text)]
            if counts:
                publications = max(counts)

        return ResearcherIndicator(
            researcher_id=None,
            year=None,
            h_index=h_index,
            publications_count=publications,
            citations_count=citations,
        )