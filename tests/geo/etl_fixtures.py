"""Ayudas de las pruebas del ETL: área de El Tintal cargada y GeoPackages sintéticos."""

import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Connection, text

from app.core.database import get_engine
from etl.load_seed import SEED
from etl.postgis_ops import load_clip_area

INSIDE = (-74.1566, 4.6448)  # IED Gabriel Betancourt Mejía, dentro de El Tintal


@pytest.fixture
def area_conn() -> Iterator[Connection]:
    """Conexión con tintal_area cargada; todo se revierte al terminar."""
    polygon = json.loads((SEED / "el_tintal_polygon.geojson").read_text(encoding="utf-8"))
    with get_engine().connect() as conn:
        tx = conn.begin()
        load_clip_area(conn, polygon["geometry"])
        yield conn
        tx.rollback()


def square_wkb(conn: Connection, x: float, y: float, d: float = 0.0002) -> bytes:
    sql = text("SELECT ST_AsBinary(ST_MakeEnvelope(:x0, :y0, :x1, :y1, 4326))")
    return bytes(conn.execute(sql, {"x0": x - d, "y0": y - d, "x1": x + d, "y1": y + d}).scalar_one())


def write_gpkg(path: Path, table: str, geom: str, column: str,
               rows: list[tuple[object, bytes, tuple[float, float, float, float]]]) -> Path:
    """GeoPackage mínimo: tabla, índice R-tree y definición de SRS 300001 (aquí EPSG:4326)."""
    pk = "fid" if table == "LOTE" else "OBJECTID"
    con = sqlite3.connect(path)
    con.execute(f'CREATE TABLE "{table}" ({pk} INTEGER PRIMARY KEY, "{geom}" BLOB, "{column}")')
    con.execute(f'CREATE VIRTUAL TABLE "rtree_{table}_{geom}" USING rtree(id, minx, maxx, miny, maxy)')
    con.execute("CREATE TABLE gpkg_spatial_ref_sys (srs_id INTEGER, definition TEXT)")
    con.execute("INSERT INTO gpkg_spatial_ref_sys VALUES (300001, 'EPSG:4326')")
    for i, (value, body, (x0, y0, x1, y1)) in enumerate(rows, start=1):
        blob = b"GP\x00\x01" + (4326).to_bytes(4, "little") + body
        con.execute(f'INSERT INTO "{table}" VALUES (?, ?, ?)', (i, blob, value))
        con.execute(f'INSERT INTO "rtree_{table}_{geom}" VALUES (?, ?, ?, ?, ?)', (i, x0, x1, y0, y1))
    con.commit()
    con.close()
    return path
