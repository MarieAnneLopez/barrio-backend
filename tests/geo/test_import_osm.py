"""ETL de extremo a extremo sin red: Overpass falso + PostGIS real + seed temporal."""

import json
from pathlib import Path
from typing import Any

import pytest

from app.core.database import get_engine
from etl.import_osm import run
from etl.tintal_config import UPZ_RELATIONS


def _ring(x0: float, y0: float, x1: float, y1: float) -> list[dict[str, float]]:
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    return [{"lon": x, "lat": y} for x, y in pts]


# Dos "UPZ" cuadradas y contiguas alrededor del centro real de El Tintal.
WEST, EAST = list(UPZ_RELATIONS)
RELATIONS = [
    {"type": "relation", "id": WEST, "members": [
        {"type": "way", "role": "outer", "geometry": _ring(-74.17, 4.645, -74.16, 4.66)}]},
    {"type": "relation", "id": EAST, "members": [
        {"type": "way", "role": "outer", "geometry": _ring(-74.16, 4.645, -74.15, 4.66)}]},
]
ROAD_ACROSS = {"type": "way", "id": 1, "tags": {"highway": "primary", "name": "Av. de prueba"},
               "geometry": [{"lon": -74.18, "lat": 4.65}, {"lon": -74.155, "lat": 4.65}]}
FAR_PARK = {"type": "way", "id": 2, "tags": {"leisure": "park"}, "geometry": _ring(-74.10, 4.70, -74.09, 4.71)}


class FakeOverpass:
    def query(self, ql: str) -> dict[str, Any]:
        if "map_to_area" not in ql:
            return {"osm3s": {"timestamp_osm_base": "2026-11-14T00:00:00Z"}, "elements": RELATIONS}
        if 'way["highway"]' in ql:
            return {"elements": [ROAD_ACROSS]}
        if "leisure" in ql:
            return {"elements": [FAR_PARK]}
        return {"elements": []}


def test_run_une_valida_recorta_y_escribe(tmp_path: Path) -> None:
    summary = run(FakeOverpass(), get_engine(), tmp_path)  # type: ignore[arg-type]

    polygon = json.loads((tmp_path / "el_tintal_polygon.geojson").read_text(encoding="utf-8"))
    assert polygon["geometry"]["type"] == "MultiPolygon"
    assert len(polygon["geometry"]["coordinates"]) == 1  # unión sin costura
    assert summary["polygon"]["area_km2"] == pytest.approx(3.67, rel=0.05)
    assert summary["layers"] == {"vias": 1, "parques": 0, "edificios": 0, "manzanas": 0}
    road = json.loads((tmp_path / "base" / "vias.geojson").read_text(encoding="utf-8"))["features"][0]
    assert road["properties"]["osm_id"] == "way/1" and road["properties"]["kind"] == "primary"
    assert road["geometry"]["coordinates"][0][0] == pytest.approx(-74.17)  # recortada al borde


def test_run_rechaza_relaciones_inesperadas(tmp_path: Path) -> None:
    class WrongIds(FakeOverpass):
        def query(self, ql: str) -> dict[str, Any]:
            return {"elements": [{**RELATIONS[0], "id": 1}]}

    with pytest.raises(ValueError, match="Relaciones esperadas"):
        run(WrongIds(), get_engine(), tmp_path)  # type: ignore[arg-type]
