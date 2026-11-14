"""CrudService: lógica de aplicación del CRUD, independiente de SQLAlchemy (DIP)."""

from collections.abc import Callable, Sequence
from typing import Any, Generic, Protocol, TypeVar

from pydantic import BaseModel

from app.core.exceptions import AppError
from app.repositories.interfaces import ReadableRepository, SpatialQueryRepository, WritableRepository
from app.repositories.query import ListQuery, Record
from app.schemas.crud import PageOut

T = TypeVar("T")


class CrudRepository(ReadableRepository[T], WritableRepository[T], SpatialQueryRepository[T], Protocol):
    """Lo que el CRUD completo necesita: la suma de las tres interfaces pequeñas."""


class NotFoundError(AppError):
    def __init__(self, slug: str, item_id: int) -> None:
        super().__init__("NOT_FOUND", f"No existe el registro {item_id} en {slug}", 404)


class CrudService(Generic[T]):
    def __init__(self, slug: str, repository: CrudRepository[T], out_schema: type[BaseModel],
                 on_delete: Sequence[Callable[[int], None]] = ()):
        self._slug = slug
        self._repository = repository
        self._out = out_schema
        # Limpiezas al borrar (calificaciones y fotos del objeto, H18).
        self._on_delete = on_delete

    def _to_out(self, record: Record[T]) -> BaseModel:
        entity = record.entity
        columns = {c.key: getattr(entity, c.key) for c in entity.__table__.columns}  # type: ignore[attr-defined]
        columns.pop("geom", None)
        return self._out.model_validate({**columns, "geometry": record.geometry})

    def list(self, query: ListQuery) -> PageOut[Any]:
        page = self._repository.list(query)
        items = [self._to_out(r) for r in page.items]
        return PageOut(items=items, total=page.total, page=page.page, size=page.size, pages=page.pages)

    def get(self, item_id: int) -> BaseModel:
        record = self._repository.get(item_id)
        if record is None:
            raise NotFoundError(self._slug, item_id)
        return self._to_out(record)

    def create(self, payload: BaseModel) -> BaseModel:
        data = payload.model_dump(exclude={"geometry"})
        geometry = payload.model_dump(include={"geometry"})["geometry"]
        return self._to_out(self._repository.create(data, geometry))

    def update(self, item_id: int, payload: BaseModel) -> BaseModel:
        data = payload.model_dump(exclude_unset=True, exclude={"geometry"})
        geometry = payload.model_dump(include={"geometry"})["geometry"] if "geometry" in payload.model_fields_set else None
        record = self._repository.update(item_id, data, geometry)
        if record is None:
            raise NotFoundError(self._slug, item_id)
        return self._to_out(record)

    def delete(self, item_id: int) -> None:
        if not self._repository.delete(item_id):
            raise NotFoundError(self._slug, item_id)
        for cleanup in self._on_delete:
            cleanup(item_id)

    def feature_collection(self, query: ListQuery) -> dict[str, Any]:
        features = []
        for record in self._repository.features(query):
            properties = self._to_out(record).model_dump(mode="json", exclude={"geometry"})
            features.append({"type": "Feature", "id": properties["id"],
                             "geometry": record.geometry, "properties": properties})
        return {"type": "FeatureCollection", "features": features}
