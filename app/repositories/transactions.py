"""Confirmación de transacciones: una restricción violada es un 409, no un 500."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError


def commit_or_conflict(session: Session, table: str) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ConflictError(table) from exc
