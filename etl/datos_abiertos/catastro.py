"""Datos abiertos → Módulo 5 · Datos Catastrales (lotes de El Tintal).

Lotes: capa Lote de la UAECD. Estrato: Manzana Estratificación de la SDP, unido
por el punto interior del lote. Sin datos personales: la matrícula inmobiliaria
no es pública, así que el campo guarda el código de lote catastral (LOTCODIGO,
D51). Avalúo, uso, pisos y área construida no se publican por lote: quedan nulos.
"""

import json
from pathlib import Path
from typing import Any

from sqlalchemy import Connection, text

from etl.datos_abiertos.gpkg import rows_in_bbox, srs_definition
from etl.datos_abiertos.sources import LOTE

SETUP = ["DROP TABLE IF EXISTS lotes, estratos",
         "CREATE TEMP TABLE lotes (code text, g geometry)",
         "CREATE TEMP TABLE estratos (e int, g geometry)"]
ENVELOPE = text("SELECT ST_XMin(b), ST_YMin(b), ST_XMax(b), ST_YMax(b) FROM "
                "(SELECT ST_Transform(ST_Envelope(g), :proj) AS b FROM tintal_area) s")
LOTE_IN = text("INSERT INTO lotes VALUES (:c, ST_SetSRID(ST_GeomFromWKB(:w), 4326))")
ESTRATO_IN = text("INSERT INTO estratos VALUES (:e, ST_Transform(ST_GeomFromWKB(:w), :proj, 4326))")
JOIN = text(
    """
    SELECT l.code, ST_AsGeoJSON(l.g, 7) AS geojson, ST_Area(l.g::geography) AS m2, s.e
    FROM lotes l JOIN tintal_area a ON ST_IsValid(l.g) AND ST_Within(l.g, a.g)
    LEFT JOIN LATERAL (SELECT e FROM estratos s WHERE ST_Contains(s.g, ST_PointOnSurface(l.g))
                       ORDER BY e LIMIT 1) s ON true
    WHERE GeometryType(l.g) = 'POLYGON' ORDER BY l.code
    """
)


def _bbox(conn: Connection, proj: str = "EPSG:4326") -> tuple[float, ...]:
    return tuple(conn.execute(ENVELOPE, {"proj": proj}).one())


def features(conn: Connection, lote_gpkg: Path, estrato_gpkg: Path) -> list[dict[str, Any]]:
    for sql in SETUP:
        conn.execute(text(sql))
    lots = [{"c": c, "w": w} for c, w in
            rows_in_bbox(lote_gpkg, "LOTE", "geom", ("LOTCODIGO",), _bbox(conn))]
    if lots:
        conn.execute(LOTE_IN, lots)
    proj = srs_definition(estrato_gpkg, 300001)
    blocks = [{"e": e, "w": w, "proj": proj} for e, w in rows_in_bbox(
        estrato_gpkg, "ManzanaEstratificacion", "Shape", ("ESTRATO",), _bbox(conn, proj))]
    if blocks:
        conn.execute(ESTRATO_IN, blocks)
    conn.execute(text("CREATE INDEX ON estratos USING gist (g)"))
    out = []
    for row in conn.execute(JOIN):
        props = {"matricula_inmobiliaria": row.code, "direccion": None,
                 "area_lote_m2": round(row.m2, 1), "area_construida_m2": None, "pisos": None,
                 "uso": None, "avaluo_cop": None,
                 "estrato": row.e if row.e and 1 <= row.e <= 6 else None,
                 "source_type": "datos_abiertos",
                 "source_ref": f"{LOTE.page}#LOTCODIGO={row.code}", "verified": True}
        out.append({"type": "Feature", "properties": props, "geometry": json.loads(row.geojson)})
    return out
