"""Datos del barrio: polígono oficial de El Tintal."""

from typing import Any

from app.repositories.interfaces import BarrioRepository
from app.schemas.barrio import BarrioPolygon


class BarrioService:
    def __init__(self, repository: BarrioRepository) -> None:
        self._repository = repository

    def polygon(self) -> BarrioPolygon:
        return BarrioPolygon.model_validate(self._repository.polygon_feature())

    def base_layer(self, name: str) -> dict[str, Any]:
        return self._repository.base_layer(name)
