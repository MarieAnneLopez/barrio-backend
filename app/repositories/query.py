"""Tipos de consulta y resultado compartidos por los repositorios CRUD."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from math import ceil
from typing import Any, Generic, TypeVar

T = TypeVar("T")

MAX_PAGE_SIZE = 100
MAX_FEATURES = 5000


@dataclass(frozen=True)
class ListQuery:
    page: int = 1
    size: int = 20
    q: str | None = None
    # "campo" ascendente o "-campo" descendente; solo campos permitidos por el módulo.
    sort: str | None = None
    filters: Mapping[str, str] = field(default_factory=dict)
    # H35: la plataforma solo muestra lo publicado; las escrituras del admin leen todo.
    include_unpublished: bool = False


@dataclass(frozen=True)
class Record(Generic[T]):
    """Entidad con su geometría ya convertida a GeoJSON (dict)."""

    entity: T
    geometry: dict[str, Any] | None


@dataclass(frozen=True)
class Page(Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int

    @property
    def pages(self) -> int:
        return ceil(self.total / self.size) if self.size else 0
