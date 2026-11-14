import pytest

from etl.osm_geometry import relation_outer_wkt, way_wkt


def _way(coords: list[tuple[float, float]], **tags: str) -> dict:
    return {
        "type": "way",
        "id": 7,
        "tags": tags,
        "geometry": [{"lon": x, "lat": y} for x, y in coords],
    }


def test_via_abierta_es_linestring() -> None:
    way = _way([(-74.15, 4.65), (-74.14, 4.66)], highway="residential")

    assert way_wkt(way) == "LINESTRING(-74.15 4.65,-74.14 4.66)"


def test_area_cerrada_es_poligono() -> None:
    ring = [(-74.15, 4.65), (-74.14, 4.65), (-74.14, 4.66), (-74.15, 4.65)]

    assert way_wkt(_way(ring, building="yes")).startswith("POLYGON((-74.15 4.65,")


def test_via_cerrada_sigue_siendo_linea() -> None:
    # Una rotonda cerrada es una vía, no un área.
    ring = [(-74.15, 4.65), (-74.14, 4.65), (-74.14, 4.66), (-74.15, 4.65)]

    assert way_wkt(_way(ring, highway="tertiary")).startswith("LINESTRING(")


def test_conjunto_cercado_sigue_siendo_area() -> None:
    # Caso real (way/1149180145): landuse=residential + barrier=yes.
    ring = [(-74.15, 4.65), (-74.14, 4.65), (-74.14, 4.66), (-74.15, 4.65)]

    wkt = way_wkt(_way(ring, landuse="residential", barrier="yes"))

    assert wkt.startswith("POLYGON((")


def test_plaza_peatonal_con_area_yes_es_poligono() -> None:
    ring = [(-74.15, 4.65), (-74.14, 4.65), (-74.14, 4.66), (-74.15, 4.65)]

    assert way_wkt(_way(ring, highway="pedestrian", area="yes")).startswith("POLYGON((")


def test_relacion_usa_solo_miembros_exteriores() -> None:
    rel = {
        "members": [
            {"type": "way", "role": "outer", "geometry": [{"lon": 1, "lat": 2}, {"lon": 3, "lat": 4}]},
            {"type": "way", "role": "inner", "geometry": [{"lon": 9, "lat": 9}, {"lon": 8, "lat": 8}]},
            {"type": "node", "role": "admin_centre"},
        ]
    }

    assert relation_outer_wkt(rel) == "MULTILINESTRING((1 2,3 4))"


def test_relacion_sin_exteriores_falla() -> None:
    with pytest.raises(ValueError, match="sin miembros exteriores"):
        relation_outer_wkt({"members": []})
