"""Polígono de El Tintal desde la semilla GeoJSON (implementa BarrioRepository).

La semilla la produce etl/import_osm.py; si en el futuro el polígono pasa a
PostGIS, basta otra implementación del mismo protocolo.
"""

import json
from functools import cached_property
from pathlib import Path
from typing import Any

from app.core.exceptions import AppError


class SeedUnavailableError(AppError):
    def __init__(self, path: Path) -> None:
        super().__init__("SEED_UNAVAILABLE", f"Falta la semilla {path.name}", 503)


class GeoJsonBarrioRepository:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._layers: dict[str, dict[str, Any]] = {}

    @cached_property
    def _feature(self) -> dict[str, Any]:
        return _read(self._path)

    def polygon_feature(self) -> dict[str, Any]:
        return self._feature

    def base_layer(self, name: str) -> dict[str, Any]:
        # `name` llega validado por la API contra una lista cerrada (sin rutas libres).
        if name not in self._layers:
            self._layers[name] = _read(self._path.parent / "base" / f"{name}.geojson")
        return self._layers[name]


def _read(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SeedUnavailableError(path) from exc
