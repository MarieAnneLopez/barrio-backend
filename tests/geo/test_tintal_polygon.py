"""El polígono semilla de El Tintal, comprobado en PostGIS (ST_Within)."""

import json
from pathlib import Path

import pytest
from sqlalchemy import Connection, text

from app.core.database import get_engine
from etl.tintal_config import CENTROID_LAT, CENTROID_LON

SEED = Path(__file__).resolve().parents[2] / "seed"
POLYGON = json.loads((SEED / "el_tintal_polygon.geojson").read_text(encoding="utf-8"))

# Puntos OSM reales (lat, lon) medidos en H7.
INSIDE = {
    "Biblioteca El Tintal": (4.6430253, -74.1547809),
    "Ciudad Tintal": (4.6540182, -74.1577659),
    "El Tintal III": (4.6558762, -74.1521144),
    "Tintal Plaza": (4.6426694, -74.1562685),
}
OUTSIDE = {
    "Vereda El Tintal Urbano (Fontibón)": (4.6649125, -74.1438049),
    "UPZ Corabastos": (4.6302610, -74.1617477),
    "UPZ Castilla": (4.6424181, -74.1429271),
}


@pytest.fixture(scope="module")
def conn() -> Connection:
    with get_engine().connect() as connection:
        yield connection


def _within(conn: Connection, lat: float, lon: float) -> bool:
    sql = text("SELECT ST_Within(ST_Point(:lon, :lat, 4326), ST_GeomFromGeoJSON(:g))")
    return bool(conn.execute(sql, {"lon": lon, "lat": lat, "g": json.dumps(POLYGON["geometry"])}).scalar())


@pytest.mark.parametrize("name", INSIDE)
def test_hitos_de_el_tintal_quedan_dentro(conn: Connection, name: str) -> None:
    assert _within(conn, *INSIDE[name]), name


@pytest.mark.parametrize("name", OUTSIDE)
def test_lugares_vecinos_quedan_fuera(conn: Connection, name: str) -> None:
    assert not _within(conn, *OUTSIDE[name]), name


def test_poligono_valido_en_srid_4326(conn: Connection) -> None:
    sql = text("SELECT ST_IsValid(g), ST_SRID(g) FROM (SELECT ST_GeomFromGeoJSON(:g) g) s")
    valid, srid = conn.execute(sql, {"g": json.dumps(POLYGON["geometry"])}).one()
    assert valid and srid == 4326


def test_centroide_y_trazabilidad() -> None:
    lon, lat = POLYGON["properties"]["centroid"]
    assert CENTROID_LAT[0] <= lat <= CENTROID_LAT[1]
    assert CENTROID_LON[0] <= lon <= CENTROID_LON[1]
    assert POLYGON["properties"]["source_type"] == "osm"
    assert "https://www.openstreetmap.org/relation/11360088" in POLYGON["properties"]["source_ref"]


@pytest.mark.parametrize("layer", ["vias", "parques", "edificios", "manzanas"])
def test_capas_base_recortadas_al_poligono(conn: Connection, layer: str) -> None:
    data = json.loads((SEED / "base" / f"{layer}.geojson").read_text(encoding="utf-8"))
    sql = text(
        "SELECT bool_and(ST_CoveredBy(ST_GeomFromGeoJSON(f), ST_Buffer(ST_GeomFromGeoJSON(:p)::geography, 1)::geometry))"
        " FROM unnest(CAST(:fs AS text[])) AS f"
    )
    features = [json.dumps(f["geometry"]) for f in data["features"]]
    assert features and all(f["properties"]["source_ref"] for f in data["features"])
    assert conn.execute(sql, {"p": json.dumps(POLYGON["geometry"]), "fs": features}).scalar()
