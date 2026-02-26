from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from cris_harvester.infrastructure.db.orm import get_engine
from cris_harvester.infrastructure.db.repositories import (
    JournalIndicatorRepository,
    JournalRepository,
    PublicationRepository,
    ResearcherRepository,
)


class SqlAlchemyUnitOfWork:
    def __init__(self, db_url: str) -> None:
        self._engine = get_engine(db_url)
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False, class_=Session)
        self.session: Session | None = None
        self._researchers: ResearcherRepository | None = None
        self._publications: PublicationRepository | None = None
        self._journals: JournalRepository | None = None
        self._journal_indicators: JournalIndicatorRepository | None = None

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self._session_factory()
        self._researchers = ResearcherRepository(self.session)
        self._publications = PublicationRepository(self.session)
        self._journals = JournalRepository(self.session)
        self._journal_indicators = JournalIndicatorRepository(self.session)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.session is None:
            return
        if exc_type:
            self.session.rollback()
        self.session.close()
        self.session = None
        self._researchers = None
        self._publications = None
        self._journals = None
        self._journal_indicators = None

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
    def publications(self) -> PublicationRepository:
        if self._publications is None:
            raise RuntimeError("UnitOfWork is not initialized")
        return self._publications

    def commit(self) -> None:
        if self.session is None:
            return
        self.session.commit()

    def rollback(self) -> None:
        if self.session is None:
            return
        self.session.rollback()
