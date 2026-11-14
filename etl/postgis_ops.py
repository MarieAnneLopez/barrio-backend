"""Operaciones geoespaciales en PostGIS para el ETL (unión de áreas y recorte)."""

import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import Connection, text

AREA_SQL = text(
    """
    WITH parts AS (
      SELECT ST_BuildArea(ST_GeomFromText(w, 4326)) AS g
      FROM unnest(CAST(:wkts AS text[])) AS w
    ), u AS (SELECT ST_Multi(ST_MakeValid(ST_Union(g))) AS g FROM parts)
    SELECT ST_AsGeoJSON(g, 7) AS geojson,
           ST_X(ST_Centroid(g)) AS lon, ST_Y(ST_Centroid(g)) AS lat,
           ST_XMin(g) AS xmin, ST_YMin(g) AS ymin, ST_XMax(g) AS xmax, ST_YMax(g) AS ymax,
           ST_Area(g::geography) / 1e6 AS km2, ST_IsValid(g) AS valid
    FROM u
    """
)

CLIP_SQL = text(
    """
    WITH src AS (
      SELECT CASE WHEN :is_relation THEN ST_BuildArea(ST_GeomFromText(:wkt, 4326))
                  ELSE ST_MakeValid(ST_GeomFromText(:wkt, 4326)) END AS g
    ), cut AS (
      SELECT ST_CollectionExtract(ST_Intersection(src.g, a.g), ST_Dimension(src.g) + 1) AS g
      FROM src, tintal_area a
      WHERE src.g IS NOT NULL AND ST_Intersects(src.g, a.g)
    )
    SELECT ST_AsGeoJSON(g, 6) FROM cut WHERE NOT ST_IsEmpty(g)
    """
)


@dataclass(frozen=True)
class AreaInfo:
    geometry: dict[str, Any]
    centroid: tuple[float, float]
    bbox: tuple[float, float, float, float]
    area_km2: float
    valid: bool


def build_area(conn: Connection, outer_wkts: list[str]) -> AreaInfo:
    """Une las áreas de varias relaciones en un MultiPolygon válido."""
    row = conn.execute(AREA_SQL, {"wkts": outer_wkts}).one()
    return AreaInfo(
        geometry=json.loads(row.geojson),
        centroid=(row.lon, row.lat),
        bbox=(row.xmin, row.ymin, row.xmax, row.ymax),
        area_km2=row.km2,
        valid=row.valid,
    )


def load_clip_area(conn: Connection, geometry: dict[str, Any]) -> None:
    """Deja el área en una tabla temporal de la conexión para recortar contra ella."""
    conn.execute(text("DROP TABLE IF EXISTS tintal_area"))
    conn.execute(
        text("CREATE TEMP TABLE tintal_area AS SELECT ST_GeomFromGeoJSON(:g) AS g"),
        {"g": json.dumps(geometry)},
    )


def clip(conn: Connection, wkt: str, is_relation: bool = False) -> dict[str, Any] | None:
    """Parte de la geometría dentro del área, o None si queda fuera."""
    result = conn.execute(CLIP_SQL, {"wkt": wkt, "is_relation": is_relation}).scalar()
    return json.loads(result) if result else None
