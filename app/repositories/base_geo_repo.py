"""BaseCrudRepository: CRUD genérico (Readable, Writable y SpatialQuery) sobre un modelo con geom;
cada módulo lo configura con sus campos de búsqueda, filtro y orden (OCP). Lee solo lo publicado (H35)."""

# Anotaciones diferidas: el método `list` tapa al tipo `list` dentro de la clase.
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.base import SRID, Base
from app.models.mixins import published
from app.repositories.filters import apply_filters, apply_search, apply_sort
from app.repositories.query import MAX_FEATURES, ListQuery, Page, Record
from app.repositories.transactions import commit_or_conflict

ModelT = TypeVar("ModelT", bound=Base)


class BaseCrudRepository(Generic[ModelT]):
    def __init__(
        self,
        session: Session,
        model: type[ModelT],
        search_fields: Sequence[str] = (),
        filter_fields: Sequence[str] = (),
        sort_fields: Sequence[str] = ("id",),
    ) -> None:
        self._session = session
        self._model = model
        self._search = [getattr(model, name) for name in search_fields]
        self._filter_fields = filter_fields
        self._sort_fields = sort_fields

    def _select(self, query: ListQuery) -> Select[Any]:
        geometry = func.ST_AsGeoJSON(self._model.geom, 7).label("geometry")  # type: ignore[attr-defined]
        stmt = select(self._model, geometry)
        if query.q and self._search:
            stmt = apply_search(stmt, self._search, query.q)
        visible = published(self._model)
        if visible is not None and not query.include_unpublished:
            stmt = stmt.where(visible)
        return apply_filters(stmt, self._model, self._filter_fields, query.filters)

    @staticmethod
    def _record(row: Any) -> Record[ModelT]:
        entity, geometry = row
        return Record(entity=entity, geometry=json.loads(geometry) if geometry else None)

    def get(self, item_id: int, include_unpublished: bool = False) -> Record[ModelT] | None:
        query = ListQuery(include_unpublished=include_unpublished)
        stmt = self._select(query).where(self._model.id == item_id)  # type: ignore[attr-defined]
        row = self._session.execute(stmt).one_or_none()
        return self._record(row) if row else None

    def list(self, query: ListQuery) -> Page[Record[ModelT]]:
        stmt = self._select(query)
        total = self._session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        stmt = apply_sort(stmt, self._model, self._sort_fields, query.sort)
        rows = self._session.execute(stmt.offset((query.page - 1) * query.size).limit(query.size))
        return Page([self._record(r) for r in rows], total, query.page, query.size)

    def features(self, query: ListQuery) -> list[Record[ModelT]]:
        stmt = apply_sort(self._select(query), self._model, self._sort_fields, query.sort)
        return [self._record(r) for r in self._session.execute(stmt.limit(MAX_FEATURES))]

    def create(self, data: Mapping[str, Any], geometry: dict[str, Any] | None) -> Record[ModelT]:
        entity = self._model(**data, geom=self._geom(geometry) if geometry else None)
        self._session.add(entity)
        commit_or_conflict(self._session, self._model.__tablename__)
        return self.get(entity.id, include_unpublished=True)  # type: ignore[attr-defined, return-value]

    def update(
        self, item_id: int, data: Mapping[str, Any], geometry: dict[str, Any] | None
    ) -> Record[ModelT] | None:
        entity = self._session.get(self._model, item_id)
        if entity is None:
            return None
        for name, value in data.items():
            setattr(entity, name, value)
        if geometry is not None:
            entity.geom = self._geom(geometry)  # type: ignore[attr-defined]
        commit_or_conflict(self._session, self._model.__tablename__)
        return self.get(item_id, include_unpublished=True)

    def delete(self, item_id: int) -> bool:
        entity = self._session.get(self._model, item_id)
        if entity is None:
            return False
        self._session.delete(entity)
        commit_or_conflict(self._session, self._model.__tablename__)
        return True

    @staticmethod
    def _geom(geometry: dict[str, Any]) -> Any:
        return func.ST_SetSRID(func.ST_GeomFromGeoJSON(json.dumps(geometry)), SRID)
