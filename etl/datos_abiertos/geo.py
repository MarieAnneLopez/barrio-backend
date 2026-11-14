"""Filtros espaciales en PostGIS para fuentes de toda la ciudad (D4).

Requieren la tabla temporal tintal_area (etl.postgis_ops.load_clip_area).
"""

import json
from typing import Any

from sqlalchemy import Connection, text

INSIDE_SQL = text(
    """
    SELECT i - 1 FROM unnest(CAST(:gs AS text[])) WITH ORDINALITY AS t(g, i), tintal_area a
    WHERE ST_Within(ST_SetSRID(ST_GeomFromGeoJSON(t.g), 4326), a.g)
    """
)
POINT_SQL = text(
    "SELECT ST_AsGeoJSON(ST_PointOnSurface(ST_BuildArea(ST_GeomFromText(:wkt, 4326))), 7)"
)


def inside(conn: Connection, features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Solo los features cuya geometría cae dentro de El Tintal, en el mismo orden."""
    if not features:
        return []
    geoms = [json.dumps(f["geometry"]) for f in features]
    keep = set(conn.execute(INSIDE_SQL, {"gs": geoms}).scalars())
    return [f for i, f in enumerate(features) if i in keep]


def point_on_surface(conn: Connection, outer_wkt: str) -> list[float]:
    """Punto interior garantizado de un área (no el centroide, que puede caer fuera)."""
    geojson = conn.execute(POINT_SQL, {"wkt": outer_wkt}).scalar_one()
    return json.loads(geojson)["coordinates"]
