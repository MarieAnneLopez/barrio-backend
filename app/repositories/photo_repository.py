"""Fotos de cada lugar (archivo local + autor + licencia) sobre PostgreSQL."""

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Foto
from app.repositories.transactions import commit_or_conflict


class SqlPhotoRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self, slug: str, objeto_id: int) -> list[Foto]:
        stmt = (select(Foto).where(Foto.categoria_slug == slug, Foto.objeto_id == objeto_id)
                .order_by(Foto.orden, Foto.id))
        return list(self._session.scalars(stmt))

    def add(self, slug: str, objeto_id: int, data: dict[str, Any]) -> Foto:
        photo = Foto(categoria_slug=slug, objeto_id=objeto_id, **data)
        self._session.add(photo)
        commit_or_conflict(self._session, "fotos")
        return photo

    def remove(self, slug: str, objeto_id: int, foto_id: int) -> bool:
        result = self._session.execute(delete(Foto).where(
            Foto.id == foto_id, Foto.categoria_slug == slug, Foto.objeto_id == objeto_id))
        commit_or_conflict(self._session, "fotos")
        return bool(result.rowcount)  # type: ignore[attr-defined]

    def forget(self, slug: str, objeto_id: int) -> None:
        """Borra las fotos de un objeto eliminado (no quedan huérfanas)."""
        self._session.execute(delete(Foto).where(Foto.categoria_slug == slug,
                                                 Foto.objeto_id == objeto_id))
        commit_or_conflict(self._session, "fotos")
