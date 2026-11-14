"""Importador genérico de módulos OSM: punto, recorte de polígonos, medida y omitidos."""

from typing import Any

from sqlalchemy import Connection

from etl.import_modules import build
from tests.geo.etl_fixtures import INSIDE, area_conn  # noqa: F401

X, Y = INSIDE


class FakeModule:
    SLUG, SELECTORS, MEASURE = "zonas-verdes", [], "area_m2"

    def __init__(self, geometry: str) -> None:
        self.GEOMETRY = geometry

    def map_element(self, element: dict[str, Any]) -> tuple[dict | None, str | None]:
        name = (element.get("tags") or {}).get("name")
        return ({"nombre": name}, None) if name else (None, "sin nombre")


def _ring(x: float, y: float, d: float) -> list[dict[str, float]]:
    pts = [(x, y), (x + d, y), (x + d, y + d), (x, y + d), (x, y)]
    return [{"lon": a, "lat": b} for a, b in pts]


def test_poligonos_dentro_con_area_y_fuera_omitidos(area_conn: Connection) -> None:
    elements = [
        {"type": "way", "id": 1, "tags": {"leisure": "park", "name": "Parque"}, "geometry": _ring(X, Y, 0.001)},
        {"type": "way", "id": 2, "tags": {"leisure": "park", "name": "Lejos"}, "geometry": _ring(-74.0, 4.7, 0.001)},
        {"type": "way", "id": 3, "tags": {"leisure": "park"}, "geometry": _ring(X, Y, 0.001)},
    ]

    result = build(FakeModule("polygon"), elements, area_conn)

    [feature] = result["features"]
    assert feature["properties"]["osm_id"] == "way/1" and feature["properties"]["area_m2"] > 12_000
    assert [(s["osm_id"], s["reason"]) for s in result["skipped"]] == \
        [("way/2", "fuera de El Tintal"), ("way/3", "sin nombre")]


def test_puntos_usan_el_centro_sin_postgis(area_conn: Connection) -> None:
    element = {"type": "node", "id": 5, "tags": {"name": "Café"}, "lat": Y, "lon": X}

    [feature] = build(FakeModule("point"), [element], area_conn)["features"]

    assert feature["geometry"] == {"type": "Point", "coordinates": [X, Y]}
    assert "area_m2" not in feature["properties"]
