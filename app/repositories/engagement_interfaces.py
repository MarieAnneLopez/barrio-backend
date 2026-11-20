"""Contratos pequeños (ISP) de calificaciones, fotos y consultas espaciales (H18).

Los servicios dependen de estos protocolos, no de SQLAlchemy (DIP); las pruebas
pueden darles dobles en memoria.
"""

from collections.abc import Sequence
from typing import Any, Protocol


class RatingRepository(Protocol):
    def add(self, slug: str, objeto_id: int, data: dict[str, Any]) -> Any: ...

    def latest(self, slug: str, objeto_id: int, limit: int) -> list[Any]: ...

    def summary(self, slug: str, objeto_id: int | None = None) -> tuple[float | None, int, int]:
        """(promedio, total de calificaciones, objetos calificados)."""
        ...

    def ranking(self, slug: str | None, limit: int) -> list[Any]:
        """Filas con categoria_slug, objeto_id, promedio y total."""
        ...

    def sync_average(self, model: Any, slug: str, objeto_id: int) -> None: ...


class PhotoRepository(Protocol):
    def list(self, slug: str, objeto_id: int) -> list[Any]: ...

    def add(self, slug: str, objeto_id: int, data: dict[str, Any]) -> Any: ...

    def remove(self, slug: str, objeto_id: int, foto_id: int) -> bool: ...


class GalleryRepository(Protocol):
    def page(self, offset: int, limit: int) -> tuple[Sequence[tuple[Any, str]], int]:
        """(pares foto y nombre del lugar, total) de los lugares publicados."""
        ...


class Forgettable(Protocol):
    """Lo que debe limpiarse cuando se elimina un objeto (calificaciones, fotos)."""

    def forget(self, slug: str, objeto_id: int) -> None: ...


class GeoInsightsRepository(Protocol):
    def nearby(self, lon: float, lat: float, radius_m: float, limit: int) -> list[tuple[int, float]]:
        """(id, distancia en metros), del más cercano al más lejano."""
        ...

    def counts(self) -> tuple[int, int, int]:
        """(total, verificados, datos de ejemplo)."""
        ...
