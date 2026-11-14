"""Sonda real de PostGIS: base disponible y base inalcanzable."""

import pytest
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import build_engine, get_engine
from app.core.exceptions import DatabaseUnavailableError
from app.repositories.health_repository import SqlDatabaseProbe


def test_la_sonda_lee_la_version_de_postgis() -> None:
    with Session(get_engine()) as session:
        version = SqlDatabaseProbe(session).postgis_version()

    assert version.startswith("3.")


def test_la_sonda_traduce_la_falla_de_conexion() -> None:
    # Puerto 1 en localhost: rechaza la conexión al instante.
    engine = build_engine(Settings(postgres_port=1, db_connect_timeout_s=1))
    with Session(engine) as session, pytest.raises(DatabaseUnavailableError):
        SqlDatabaseProbe(session).postgis_version()
    engine.dispose()
