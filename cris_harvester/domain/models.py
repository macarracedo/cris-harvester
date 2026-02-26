from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BaseEntity(BaseModel):
    source_portal: str = Field(..., description="Portal source identifier")
    source_url: str = Field(..., description="Canonical source URL")


class Researcher(BaseModel):
    source_portal: str
    url_id: Optional[int] = None
    name: str
    orcid: Optional[str] = None
    email: Optional[str] = None
    department_name: Optional[str] = None
    center_name: Optional[str] = None
    campus_name: Optional[str] = None
    area_name: Optional[str] = None
    research_group_name: Optional[str] = None
    department_id: Optional[int] = None
    center_id: Optional[int] = None
    campus_id: Optional[int] = None
    area_id: Optional[int] = None
    research_group_id: Optional[int] = None


class AuthorRef(BaseModel):
    name: str
    url_id: Optional[int] = None
    orcid: Optional[str] = None


class Department(BaseModel):
    source_portal: str
    name: str


class Center(BaseModel):
    source_portal: str
    name: str


class Campus(BaseModel):
    source_portal: str
    name: str


class Area(BaseModel):
    source_portal: str
    name: str


class ResearchGroup(BaseModel):
    source_portal: str
    name: str


class Journal(BaseEntity):
    issn: str
    title: Optional[str] = None


class JournalIndicator(BaseModel):
    journal_issn: Optional[str] = None
    journal_id: Optional[int] = None
    year: Optional[int] = None
    metrics: dict[str, str] = Field(default_factory=dict)


class ResearcherIndicator(BaseModel):
    researcher_id: Optional[int] = None
    year: Optional[int] = None
    h_index: Optional[int] = None
    publications_count: Optional[int] = None
    citations_count: Optional[int] = None


class Publication(BaseEntity):
    title: str
    document_code: str
    year: Optional[int] = None
    doi: Optional[str] = None
    publication_date: Optional[str] = None
    journal_id: Optional[int] = None
    journal_title: Optional[str] = None
    journal_issn: Optional[str] = None
    indicator_url: Optional[str] = None
    authors: list[AuthorRef] = Field(default_factory=list)


class ScheduledTask(BaseModel):
    id: Optional[int] = None
    task_type: str
    portal: str
    entity: Optional[str] = None
    limit: Optional[int] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    with_researcher_indicators: bool = False
    start_at: datetime
    frequency_days: int
    end_at: Optional[datetime] = None
    max_runs: Optional[int] = None
    run_count: int = 0
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    status: str = "active"
