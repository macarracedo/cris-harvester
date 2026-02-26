from __future__ import annotations

import re
from urllib.parse import urljoin

from selectolax.lexbor import LexborHTMLParser


_whitespace_re = re.compile(r"\s+")


def normalize_space(text: str) -> str:
    return _whitespace_re.sub(" ", text or "").strip()


def safe_text(node) -> str:
    if node is None:
        return ""
    return normalize_space(node.text())


def select_first_text(parser: LexborHTMLParser, selectors: list[str]) -> str:
    for selector in selectors:
        node = parser.css_first(selector)
        value = safe_text(node)
        if value:
            return value
    return ""


def to_abs_url(base_url: str, href: str) -> str:
    return urljoin(base_url, href)


def normalize_doi(doi: str) -> str:
    value = normalize_space(doi)
    if not value:
        return ""
    value = value.replace("https://doi.org/", "").replace("http://doi.org/", "")
    value = value.replace("doi:", "").replace("DOI:", "")
    return normalize_space(value)


def split_person_name(full_name: str) -> tuple[str, str]:
    name = normalize_space(full_name)
    if not name:
        return "", ""

    if "," in name:
        family, given = [part.strip() for part in name.split(",", maxsplit=1)]
        return given, family

    parts = name.split(" ")
    if len(parts) == 1:
        return parts[0], ""
    if len(parts) == 2:
        return parts[0], parts[1]
    return parts[0], " ".join(parts[1:])
