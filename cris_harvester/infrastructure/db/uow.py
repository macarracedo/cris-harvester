from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from cris_harvester.infrastructure.db.orm import get_engine
from cris_harvester.infrastructure.db.repositories import (
    AreaRepository,
    CampusRepository,
    CenterRepository,
    DepartmentRepository,
    JournalIndicatorRepository,
    JournalRepository,
    PublicationRepository,
    ResearchGroupRepository,
    ResearcherIndicatorRepository,
    ResearcherPublicationRepository,
    ResearcherRepository,
    ScheduledTaskRepository,
)


class SqlAlchemyUnitOfWork:
    def __init__(self, db_url: str) -> None:
        self._engine = get_engine(db_url)
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False, class_=Session)
        self.session: Session | None = None
        self._researchers: ResearcherRepository | None = None
        self._departments: DepartmentRepository | None = None
        self._centers: CenterRepository | None = None
        self._campuses: CampusRepository | None = None
        self._areas: AreaRepository | None = None
        self._research_groups: ResearchGroupRepository | None = None
        self._publications: PublicationRepository | None = None
        self._journals: JournalRepository | None = None
        self._journal_indicators: JournalIndicatorRepository | None = None
        self._researcher_publications: ResearcherPublicationRepository | None = None
        self._researcher_indicators: ResearcherIndicatorRepository | None = None
        self._scheduled_tasks: ScheduledTaskRepository | None = None

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self._session_factory()
        self._researchers = ResearcherRepository(self.session)
        self._departments = DepartmentRepository(self.session)
        self._centers = CenterRepository(self.session)
        self._campuses = CampusRepository(self.session)
        self._areas = AreaRepository(self.session)
        self._research_groups = ResearchGroupRepository(self.session)
        self._publications = PublicationRepository(self.session)
        self._journals = JournalRepository(self.session)
        self._journal_indicators = JournalIndicatorRepository(self.session)
        self._researcher_publications = ResearcherPublicationRepository(self.session)
        self._researcher_indicators = ResearcherIndicatorRepository(self.session)
        self._scheduled_tasks = ScheduledTaskRepository(self.session)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.session is None:
            return
        if exc_type:
            self.session.rollback()
        self.session.close()
        self.session = None
        self._researchers = None
        self._departments = None
        self._centers = None
        self._campuses = None
        self._areas = None
        self._research_groups = None
        self._publications = None
        self._journals = None
        self._journal_indicators = None
        self._researcher_publications = None
        self._researcher_indicators = None
        self._scheduled_tasks = None

    @property
    def journals(self) -> JournalRepository:
        if self._journals is None:
            raise RuntimeError("UnitOfWork is not initialized")
        return self._journals

    @property
    def journal_indicators(self) -> JournalIndicatorRepository:
        if self._journal_indicators is None:
            raise RuntimeError("UnitOfWork is not initialized")
        return self._journal_indicators

    @property
    def researchers(self) -> ResearcherRepository:
        if self._researchers is None:
            raise RuntimeError("UnitOfWork is not initialized")
        return self._researchers

    @property
    def departments(self) -> DepartmentRepository:
        if self._departments is None:
            raise RuntimeError("UnitOfWork is not initialized")
        return self._departments

    @property
    def centers(self) -> CenterRepository:
        if self._centers is None:
            raise RuntimeError("UnitOfWork is not initialized")
        return self._centers

    @property
    def campuses(self) -> CampusRepository:
        if self._campuses is None:
            raise RuntimeError("UnitOfWork is not initialized")
        return self._campuses

    @property
    def areas(self) -> AreaRepository:
        if self._areas is None:
            raise RuntimeError("UnitOfWork is not initialized")
        return self._areas

    @property
    def research_groups(self) -> ResearchGroupRepository:
        if self._research_groups is None:
            raise RuntimeError("UnitOfWork is not initialized")
        return self._research_groups

    @property
    def publications(self) -> PublicationRepository:
        if self._publications is None:
            raise RuntimeError("UnitOfWork is not initialized")
        return self._publications

    @property
    def researcher_publications(self) -> ResearcherPublicationRepository:
        if self._researcher_publications is None:
            raise RuntimeError("UnitOfWork is not initialized")
        return self._researcher_publications

    @property
    def researcher_indicators(self) -> ResearcherIndicatorRepository:
        if self._researcher_indicators is None:
            raise RuntimeError("UnitOfWork is not initialized")
        return self._researcher_indicators

    @property
    def scheduled_tasks(self) -> ScheduledTaskRepository:
        if self._scheduled_tasks is None:
            raise RuntimeError("UnitOfWork is not initialized")
        return self._scheduled_tasks

    def commit(self) -> None:
        if self.session is None:
            return
        self.session.commit()

    def rollback(self) -> None:
        if self.session is None:
            return
        self.session.rollback()
