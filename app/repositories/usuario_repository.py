"""Usuarios en PostgreSQL; el correo se guarda y se busca en minúsculas."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.usuario import Usuario


class EmailTakenError(Exception):
    """El correo ya tiene una cuenta (también si dos registros chocan a la vez)."""


class SqlUsuarioRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def by_email(self, email: str) -> Usuario | None:
        return self._session.scalar(select(Usuario).where(Usuario.email == email.lower()))

    def get(self, user_id: int) -> Usuario | None:
        return self._session.get(Usuario, user_id)

    def add(self, usuario: Usuario) -> Usuario:
        usuario.email = usuario.email.lower()
        self._session.add(usuario)
        try:
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise EmailTakenError from exc
        self._session.refresh(usuario)
        return usuario
