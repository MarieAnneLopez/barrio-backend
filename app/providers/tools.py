"""Herramientas del agente: lo que los modelos pueden consultar del barrio (ISP/DIP).

Los modelos dependen de este protocolo, no de SQLAlchemy; la implementación
real está en app/repositories/barrio_tools.py y las pruebas usan un doble.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ModuleSummary:
    slug: str
    total: int
    verified: int
    ejemplos: tuple[str, ...]


@dataclass(frozen=True)
class RankedPlace:
    slug: str
    objeto_id: int
    nombre: str
    promedio: float
    votos: int


@dataclass(frozen=True)
class NearPlace:
    slug: str
    objeto_id: int
    nombre: str
    distancia_m: float


@dataclass(frozen=True)
class Milestone:
    anio: int
    titulo: str
    verified: bool


@dataclass(frozen=True)
class Locality:
    nombre: str
    poblacion: int | None
    superficie_km2: float | None


class BarrioTools(Protocol):
    def summary(self, slug: str) -> ModuleSummary: ...
    def place_names(self, slug: str) -> list[tuple[str, str]]: ...
    def totals(self) -> dict[str, int]: ...
    def ratings_count(self) -> int: ...
    def best(self, slug: str | None) -> RankedPlace | None: ...
    def nearest(self, lon: float, lat: float, slug: str | None, limit: int = 3) -> list[NearPlace]: ...
    def milestones(self) -> list[Milestone]: ...
    def locality(self) -> Locality | None: ...
    def center(self) -> tuple[float, float]: ...
