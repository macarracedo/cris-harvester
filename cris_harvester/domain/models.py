from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class BaseEntity(BaseModel):
    source_portal: str = Field(..., description="Portal source identifier")
    source_url: str = Field(..., description="Canonical source URL")


class Researcher(BaseEntity):
    name: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    orcid: Optional[str] = None


class AuthorRef(BaseModel):
    name: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    source_url: Optional[str] = None
    orcid: Optional[str] = None


class Journal(BaseEntity):
    issn: str
    title: Optional[str] = None


class JournalIndicator(BaseEntity):
    journal_issn: str
    year: Optional[int] = None
    metrics: dict[str, str] = Field(default_factory=dict)


class Publication(BaseEntity):
    title: str
    year: Optional[int] = None
    doi: Optional[str] = None
    publication_date: Optional[str] = None
    journal_title: Optional[str] = None
    journal_issn: Optional[str] = None
    indicator_url: Optional[str] = None
    authors: list[AuthorRef] = Field(default_factory=list)
