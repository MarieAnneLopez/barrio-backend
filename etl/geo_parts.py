"""Recorte de polígonos y líneas OSM contra El Tintal, conservando la parte mayor.

Los esquemas piden POLYGON / LINESTRING simples: si el recorte deja varias
partes se guarda la de mayor área (o longitud). Se recorta contra el área
encogida 2e-6° (≈ 0,2 m) para que el redondeo a 7 decimales no saque vértices
del polígono, que load_seed vuelve a exigir con ST_Within. Lo que ya está
contenido no se interseca: GEOS 3.9.0 (imagen postgis 16-3.4) devuelve vacía la
intersección de algunas líneas horizontales contenidas.
"""

import json
from typing import Any

from sqlalchemy import Connection, text

DIMENSION = {"polygon": 3, "line": 2}
PART_SQL = text(
    """
    WITH src AS (
      SELECT CASE WHEN :is_relation THEN ST_BuildArea(ST_GeomFromText(:wkt, 4326))
                  ELSE ST_MakeValid(ST_GeomFromText(:wkt, 4326)) END AS g
    ), inner_area AS (SELECT ST_Buffer(g, -0.000002) AS g FROM tintal_area
    ), cut AS (
      SELECT CASE WHEN ST_Contains(a.g, src.g) THEN src.g
                  ELSE ST_CollectionExtract(ST_Intersection(src.g, a.g), :dim) END AS g
      FROM src, inner_area a
      WHERE src.g IS NOT NULL AND ST_Intersects(src.g, a.g)
    ), parts AS (
      SELECT (ST_Dump(CASE WHEN :dim = 2 THEN ST_LineMerge(g) ELSE g END)).geom AS g FROM cut
    )
    SELECT ST_AsGeoJSON(g, 7) AS geojson,
           CASE WHEN :dim = 3 THEN ST_Area(g::geography) ELSE ST_Length(g::geography) END AS m
    FROM parts WHERE NOT ST_IsEmpty(g) ORDER BY m DESC LIMIT 1
    """
)


def largest_part(conn: Connection, wkt: str, kind: str, is_relation: bool = False
                 ) -> tuple[dict[str, Any], float] | None:
    """(GeoJSON de la parte mayor dentro de El Tintal, área m² o longitud m), o None."""
    row = conn.execute(PART_SQL, {"wkt": wkt, "is_relation": is_relation,
                                  "dim": DIMENSION[kind]}).first()
    if row is None or row.geojson is None:
        return None
    return json.loads(row.geojson), float(row.m)
