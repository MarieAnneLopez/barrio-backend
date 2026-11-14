"""Sonda de base de datos sobre SQLAlchemy (implementa DatabaseProbe)."""

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import DatabaseUnavailableError


class SqlDatabaseProbe:
    def __init__(self, session: Session) -> None:
        self._session = session

    def postgis_version(self) -> str:
        try:
            return str(self._session.execute(text("SELECT PostGIS_Version()")).scalar_one())
        except SQLAlchemyError as exc:
            raise DatabaseUnavailableError() from exc
