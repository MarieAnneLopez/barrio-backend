"""¿Una geometría cae dentro de El Tintal? (UPZ 78 + 79, D38/D63). Lo usan el CRUD y el ETL."""

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

WITHIN = text("SELECT ST_Within(ST_GeomFromGeoJSON(:g), ST_GeomFromGeoJSON(:area))")


class SqlTintalArea:
    def __init__(self, session: Session, polygon: dict[str, Any]) -> None:
        self._session = session
        self._area = json.dumps(polygon)

    def contains(self, geometry: dict[str, Any]) -> bool:
        return bool(self._session.execute(WITHIN, {"g": json.dumps(geometry), "area": self._area}).scalar())
