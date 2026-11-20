"""Contratos pequeños y específicos (ISP) de los que dependen los servicios (DIP).

Las implementaciones concretas viven en este mismo paquete; los servicios
solo conocen estos protocolos.
"""

from collections.abc import Mapping
from typing import Any, Protocol, TypeVar

from app.repositories.query import ListQuery, Page, Record

T = TypeVar("T")


class DatabaseProbe(Protocol):
    """Comprueba que la base responde y tiene PostGIS."""

    def postgis_version(self) -> str:
        """Versión de PostGIS; lanza DatabaseUnavailableError si la base no responde."""
        ...


class BarrioRepository(Protocol):
    """Fuente del polígono oficial de El Tintal (GeoJSON Feature, SRID 4326)."""

    def polygon_feature(self) -> dict[str, Any]:
        """Feature con geometry, bbox y properties de trazabilidad."""
        ...

    def base_layer(self, name: str) -> dict[str, Any]:
        """FeatureCollection de una capa base del mapa (vias, parques, edificios, manzanas)."""
        ...


class ReadableRepository(Protocol[T]):
    """Consulta: detalle y lista paginada con búsqueda, filtros y orden."""

    def get(self, item_id: int, include_unpublished: bool = False) -> Record[T] | None: ...

    def list(self, query: ListQuery) -> Page[Record[T]]: ...


class WritableRepository(Protocol[T]):
    """Escritura; la geometría llega como GeoJSON y se guarda en SRID 4326."""

    def create(self, data: Mapping[str, Any], geometry: dict[str, Any] | None) -> Record[T]: ...

    def update(
        self, item_id: int, data: Mapping[str, Any], geometry: dict[str, Any] | None
    ) -> Record[T] | None: ...

    def delete(self, item_id: int) -> bool: ...


class SpatialQueryRepository(Protocol[T]):
    """Consultas espaciales: colección completa para el mapa."""

    def features(self, query: ListQuery) -> list[Record[T]]: ...
