"""OSM + datos abiertos → Módulo 11 · Información de la Localidad de Kennedy (ficha).

Límite: relación OSM de la localidad (admin_level 8). Población: proyección de
la SDS para el año de POBLACION_ANIO. Alcaldía: capa de la Secretaría de
Gobierno. Historia, bandera y retos se documentan con fuentes en H20; hasta
entonces quedan nulos, no inventados.
"""

import csv
import io
import json
from typing import Any

from sqlalchemy import Connection, text

from etl.datos_abiertos.sources import ALCALDIA, POBLACION
from etl.tintal_config import osm_url

KENNEDY_RELATION = 4740229
KENNEDY_CODE = "8"
POBLACION_ANIO = 2026
AREA_SQL = text(
    "SELECT ST_AsGeoJSON(g, 6), ST_Area(g::geography) / 1e6 FROM (SELECT ST_Multi("
    "ST_SimplifyPreserveTopology(ST_BuildArea(ST_GeomFromText(:wkt, 4326)), 0.00002)) AS g) s"
)


def population(csv_text: str, year: int = POBLACION_ANIO) -> int:
    rows = csv.DictReader(io.StringIO(csv_text), delimiter=";")
    return sum(int(r["POBLACION"]) for r in rows
               if r["CODIGO_LOCALIDAD"] == KENNEDY_CODE and int(r["ANO"]) == year)


def alcaldia(data: dict[str, Any]) -> str:
    for f in data["features"]:
        a = f["attributes"]
        if a.get("COD_LOC") == "08":
            return f"{a['NOM_ALCALDIA'].strip()}, {a['DIRECCION'].strip()}"
    raise ValueError("La capa de alcaldías no trae la de Kennedy (COD_LOC 08)")


def feature(conn: Connection, outer_wkt: str, csv_text: str, alcaldias: dict[str, Any]
            ) -> dict[str, Any]:
    geojson, km2 = conn.execute(AREA_SQL, {"wkt": outer_wkt}).one()
    refs = [osm_url("relation", KENNEDY_RELATION), POBLACION.page, ALCALDIA.page]
    props = {
        "nombre_localidad": "Kennedy", "bandera_url": None, "historia": None,
        "poblacion": population(csv_text), "superficie_km2": round(km2, 2),
        "alcaldia_local": alcaldia(alcaldias)[:200], "retos": None,
        "source_type": "datos_abiertos", "source_ref": " | ".join(refs), "verified": True,
    }
    return {"type": "Feature", "properties": props, "geometry": json.loads(geojson)}
