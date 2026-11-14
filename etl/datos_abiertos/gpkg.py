"""Lectura mínima de GeoPackage (SQLite) sin dependencias: filtro por índice R-tree.

La geometría GPKG es un encabezado (magic "GP", versión, flags, srs_id y un
sobre opcional) seguido de WKB estándar; PostGIS lee el WKB directamente.
"""

import sqlite3
from collections.abc import Iterator
from pathlib import Path

ENVELOPE_BYTES = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}


def wkb(blob: bytes) -> bytes:
    """WKB de una geometría GPKG (OGC 12-128r18, §2.1.3)."""
    if blob[:2] != b"GP":
        raise ValueError("No es una geometría GeoPackage")
    envelope = (blob[3] >> 1) & 0x07
    return blob[8 + ENVELOPE_BYTES[envelope]:]


def rows_in_bbox(path: Path, table: str, geom: str, columns: tuple[str, ...],
                 bbox: tuple[float, float, float, float]) -> Iterator[tuple]:
    """(columnas..., wkb) de las filas cuyo sobre cae completo dentro del bbox."""
    pk = "fid" if table == "LOTE" else "OBJECTID"
    cols = ", ".join(f't."{c}"' for c in columns)
    sql = (f'SELECT {cols}, t."{geom}" FROM "{table}" t JOIN "rtree_{table}_{geom}" r '
           f"ON t.{pk} = r.id WHERE r.minx >= ? AND r.maxx <= ? AND r.miny >= ? AND r.maxy <= ?")
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        xmin, ymin, xmax, ymax = bbox
        for row in con.execute(sql, (xmin, xmax, ymin, ymax)):
            if row[-1] is not None:
                yield (*row[:-1], wkb(row[-1]))
    finally:
        con.close()


def srs_definition(path: Path, srs_id: int) -> str:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return con.execute("SELECT definition FROM gpkg_spatial_ref_sys WHERE srs_id = ?",
                           (srs_id,)).fetchone()[0]
    finally:
        con.close()
