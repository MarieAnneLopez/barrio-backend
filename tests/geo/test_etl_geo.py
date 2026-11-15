"""ETL en PostGIS real: recorte por partes, filtros, catastro y ejemplos reproducibles."""

import json
from pathlib import Path

from sqlalchemy import Connection

from etl import examples
from etl.datos_abiertos import catastro
from etl.datos_abiertos.geo import inside, point_on_surface
from etl.geo_parts import largest_part
from etl.load_seed import SEED
from tests.geo.etl_fixtures import INSIDE, area_conn, square_wkb, write_gpkg  # noqa: F401

X, Y = INSIDE


def _pt(x: float, y: float) -> dict:
    return {"type": "Feature", "properties": {}, "geometry": {"type": "Point", "coordinates": [x, y]}}


def test_largest_part_recorta_y_mide(area_conn: Connection) -> None:
    square = f"POLYGON(({X} {Y},{X + 0.001} {Y},{X + 0.001} {Y + 0.001},{X} {Y + 0.001},{X} {Y}))"
    line = f"LINESTRING({X} {Y},{X + 0.001} {Y})"

    polygon, m2 = largest_part(area_conn, square, "polygon")  # type: ignore[misc]
    road, meters = largest_part(area_conn, line, "line")  # type: ignore[misc]

    assert polygon["type"] == "Polygon" and 12_000 < m2 < 12_500
    assert road["type"] == "LineString" and 105 < meters < 115
    assert largest_part(area_conn, "LINESTRING(-74.0 4.7,-74.01 4.7)", "line") is None


def test_inside_conserva_el_orden_y_point_on_surface(area_conn: Connection) -> None:
    kept = inside(area_conn, [_pt(-74.0, 4.7), _pt(X, Y), _pt(X + 0.0001, Y)])
    lon, lat = point_on_surface(area_conn, f"MULTILINESTRING(({X} {Y},{X + 0.01} {Y},"
                                           f"{X + 0.01} {Y + 0.01},{X} {Y + 0.01},{X} {Y}))")

    assert [f["geometry"]["coordinates"][0] for f in kept] == [X, X + 0.0001]
    assert inside(area_conn, []) == []
    assert X < lon < X + 0.01 and Y < lat < Y + 0.01


def test_catastro_lotes_dentro_con_estrato_y_sin_datos_personales(
        area_conn: Connection, tmp_path: Path) -> None:
    lot = square_wkb(area_conn, X, Y)
    box = (X - 0.0002, Y - 0.0002, X + 0.0002, Y + 0.0002)
    lotes = write_gpkg(tmp_path / "l.gpkg", "LOTE", "geom", "LOTCODIGO", [("008519073023", lot, box)])
    block = square_wkb(area_conn, X, Y, 0.001)
    estratos = write_gpkg(tmp_path / "e.gpkg", "ManzanaEstratificacion", "Shape", "ESTRATO",
                          [(2, block, (X - 0.001, Y - 0.001, X + 0.001, Y + 0.001))])

    [feature] = catastro.features(area_conn, lotes, estratos)
    p = feature["properties"]

    assert p["codigo_lote"] == "008519073023" and p["estrato"] == 2
    assert 1_900 < p["area_lote_m2"] < 2_100 and p["avaluo_cop"] is None
    assert p["source_ref"].endswith("#LOTCODIGO=008519073023") and feature["geometry"]["type"] == "Polygon"


def test_ejemplos_reproducibles_dentro_y_sin_duplicar(area_conn: Connection, tmp_path: Path) -> None:
    (tmp_path / "modules").mkdir()
    (tmp_path / "el_tintal_polygon.geojson").write_bytes((SEED / "el_tintal_polygon.geojson").read_bytes())
    path = tmp_path / "modules" / "veterinarias.geojson"

    assert examples.complete(area_conn, "veterinarias", tmp_path) == 3
    first = path.read_text(encoding="utf-8")
    assert examples.complete(area_conn, "veterinarias", tmp_path) == 3
    data = json.loads(path.read_text(encoding="utf-8"))

    assert path.read_text(encoding="utf-8") == first and len(data["features"]) == 3
    assert all(f["properties"]["source_type"] == "seed" and not f["properties"]["verified"]
               for f in data["features"])
    assert len(inside(area_conn, data["features"])) == 3
