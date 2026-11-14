"""Hitos desde PostGIS (tabla historia_hitos) y catálogo de fuentes desde la semilla.

Implementa HistoriaRepository. Los hitos los carga etl/load_historia.py desde
seed/historia.json; el catálogo de fuentes vive en ese mismo archivo.
"""

import json
from functools import cached_property
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.historia_hito import HistoriaHito
from app.repositories.barrio_repository import SeedUnavailableError


class SqlHistoriaRepository:
    def __init__(self, session: Session, catalog: Path) -> None:
        self._session = session
        self._catalog = catalog

    def hitos(self) -> list[HistoriaHito]:
        query = select(HistoriaHito).order_by(HistoriaHito.anio, HistoriaHito.orden, HistoriaHito.id)
        return list(self._session.scalars(query))

    @cached_property
    def _data(self) -> dict[str, Any]:
        try:
            return json.loads(self._catalog.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise SeedUnavailableError(self._catalog) from exc

    def fuentes(self) -> list[dict[str, Any]]:
        return list(self._data["fuentes"])

    def consultado(self) -> str:
        return str(self._data["consultado"])
