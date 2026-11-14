"""Cableado de dependencias: los endpoints reciben abstracciones vía Depends."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.repositories.health_repository import SqlDatabaseProbe
from app.repositories.interfaces import DatabaseProbe
from app.services.health_service import HealthService

SessionDep = Annotated[Session, Depends(get_session)]


def get_db_probe(session: SessionDep) -> DatabaseProbe:
    return SqlDatabaseProbe(session)


def get_health_service(probe: Annotated[DatabaseProbe, Depends(get_db_probe)]) -> HealthService:
    return HealthService(probe)
