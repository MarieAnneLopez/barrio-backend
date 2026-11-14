"""Cableado de dependencias: los endpoints reciben abstracciones vía Depends."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_session
from app.repositories.barrio_repository import GeoJsonBarrioRepository
from app.repositories.health_repository import SqlDatabaseProbe
from app.repositories.interfaces import BarrioRepository, DatabaseProbe
from app.services.barrio_service import BarrioService
from app.services.health_service import HealthService

SessionDep = Annotated[Session, Depends(get_session)]


def get_db_probe(session: SessionDep) -> DatabaseProbe:
    return SqlDatabaseProbe(session)


def get_health_service(probe: Annotated[DatabaseProbe, Depends(get_db_probe)]) -> HealthService:
    return HealthService(probe)


@lru_cache
def get_barrio_repository() -> BarrioRepository:
    """Una sola lectura de la semilla por proceso."""
    return GeoJsonBarrioRepository(get_settings().seed_dir / "el_tintal_polygon.geojson")


def get_barrio_service(
    repository: Annotated[BarrioRepository, Depends(get_barrio_repository)],
) -> BarrioService:
    return BarrioService(repository)
