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

    @cached_property
    def _feature(self) -> dict[str, Any]:
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise SeedUnavailableError(self._path) from exc

    def polygon_feature(self) -> dict[str, Any]:
        return self._feature
