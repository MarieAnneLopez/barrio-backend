"""Calificaciones polimórficas (categoria_slug + objeto_id) sobre PostgreSQL."""

from decimal import Decimal
from typing import Any

from sqlalchemy import Row, delete, func, select, update
from sqlalchemy.orm import Session

from app.models import Calificacion as Rated
from app.models.base import Base
from app.repositories.transactions import commit_or_conflict


class SqlRatingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, slug: str, objeto_id: int, data: dict[str, Any]) -> Rated:
        rating = Rated(categoria_slug=slug, objeto_id=objeto_id, **data)
        self._session.add(rating)
        commit_or_conflict(self._session, "calificaciones")
        return rating

    def latest(self, slug: str, objeto_id: int, limit: int) -> list[Rated]:
        stmt = (select(Rated).where(Rated.categoria_slug == slug, Rated.objeto_id == objeto_id)
                .order_by(Rated.created_at.desc(), Rated.id.desc()).limit(limit))
        return list(self._session.scalars(stmt))

    def summary(self, slug: str, objeto_id: int | None = None) -> tuple[float | None, int, int]:
        """(promedio, total de calificaciones, objetos calificados) del módulo u objeto."""
        stmt = select(func.avg(Rated.estrellas), func.count(),
                      func.count(func.distinct(Rated.objeto_id))).where(Rated.categoria_slug == slug)
        if objeto_id is not None:
            stmt = stmt.where(Rated.objeto_id == objeto_id)
        avg, total, objects = self._session.execute(stmt).one()
        return (round(float(avg), 2) if avg is not None else None), total, objects

    def ranking(self, slug: str | None, limit: int) -> list[Row[Any]]:
        """(categoria_slug, objeto_id, promedio, total) de mejor a peor; desempata por votos."""
        avg = func.avg(Rated.estrellas)
        stmt = (select(Rated.categoria_slug, Rated.objeto_id, avg.label("promedio"),
                       func.count().label("total"))
                .group_by(Rated.categoria_slug, Rated.objeto_id)
                .order_by(avg.desc(), func.count().desc(), Rated.categoria_slug, Rated.objeto_id)
                .limit(limit))
        if slug is not None:
            stmt = stmt.where(Rated.categoria_slug == slug)
        return list(self._session.execute(stmt))

    def sync_average(self, model: type[Base], slug: str, objeto_id: int) -> None:
        """Copia el promedio a calificacion_promedio en los módulos que lo tienen (§11.3)."""
        if "calificacion_promedio" not in model.__table__.columns:
            return
        avg, _, _ = self.summary(slug, objeto_id)
        value = Decimal(str(round(avg, 1))) if avg is not None else None
        self._session.execute(update(model).where(model.id == objeto_id)  # type: ignore[attr-defined]
                              .values(calificacion_promedio=value))
        commit_or_conflict(self._session, model.__tablename__)

    def forget(self, slug: str, objeto_id: int) -> None:
        """Borra las calificaciones de un objeto eliminado (no quedan huérfanas)."""
        self._session.execute(delete(Rated).where(Rated.categoria_slug == slug,
                                                  Rated.objeto_id == objeto_id))
        commit_or_conflict(self._session, "calificaciones")
