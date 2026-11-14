import pytest
from pydantic import ValidationError

from app.schemas.geojson import geometry_schema

SQUARE = [[-74.16, 4.65], [-74.15, 4.65], [-74.15, 4.66], [-74.16, 4.65]]


def test_punto_valido() -> None:
    point = geometry_schema("POINT").model_validate({"type": "Point", "coordinates": [-74.15, 4.65]})

    assert point.model_dump() == {"type": "Point", "coordinates": [-74.15, 4.65]}


@pytest.mark.parametrize(
    "coords",
    [[-200, 4.65], [-74.15, 95], [-74.15], ["a", 4.65], [-74.15, 4.65, 2600, 1]],
)
def test_punto_fuera_de_rango_o_malformado(coords: list) -> None:
    with pytest.raises(ValidationError):
        geometry_schema("POINT").model_validate({"type": "Point", "coordinates": coords})


def test_tipo_de_geometria_debe_coincidir_con_el_modulo() -> None:
    with pytest.raises(ValidationError):
        geometry_schema("POINT").model_validate({"type": "Polygon", "coordinates": [SQUARE]})


def test_linea_necesita_dos_posiciones() -> None:
    schema = geometry_schema("LINESTRING")
    schema.model_validate({"type": "LineString", "coordinates": SQUARE[:2]})
    with pytest.raises(ValidationError, match="2 posiciones"):
        schema.model_validate({"type": "LineString", "coordinates": SQUARE[:1]})


def test_poligono_exige_anillos_cerrados() -> None:
    schema = geometry_schema("POLYGON")
    schema.model_validate({"type": "Polygon", "coordinates": [SQUARE]})
    with pytest.raises(ValidationError, match="cerrado"):
        schema.model_validate({"type": "Polygon", "coordinates": [SQUARE[:3] + [[-74.1, 4.6]]]})


def test_multipoligono_valida_cada_poligono() -> None:
    schema = geometry_schema("MULTIPOLYGON")
    schema.model_validate({"type": "MultiPolygon", "coordinates": [[SQUARE]]})
    with pytest.raises(ValidationError):
        schema.model_validate({"type": "MultiPolygon", "coordinates": [[SQUARE[:2]]]})
