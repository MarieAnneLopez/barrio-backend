"""Geometrías GeoJSON (RFC 7946, lon/lat WGS84) validadas en el borde de la API."""

from functools import cache
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, model_validator

GEOJSON_NAMES = {
    "POINT": "Point",
    "LINESTRING": "LineString",
    "POLYGON": "Polygon",
    "MULTIPOLYGON": "MultiPolygon",
}


def _position(value: Any) -> None:
    ok = (
        isinstance(value, list)
        and len(value) in (2, 3)
        and all(isinstance(v, int | float) and not isinstance(v, bool) for v in value)
    )
    if not ok or not (-180 <= value[0] <= 180 and -90 <= value[1] <= 90):
        raise ValueError("Cada posición es [lon, lat] en grados decimales WGS84")


def _line(coords: Any, minimum: int = 2) -> None:
    if not isinstance(coords, list) or len(coords) < minimum:
        raise ValueError(f"Una línea necesita al menos {minimum} posiciones")
    for position in coords:
        _position(position)


def _polygon(coords: Any) -> None:
    if not isinstance(coords, list) or not coords:
        raise ValueError("Un polígono necesita al menos un anillo")
    for ring in coords:
        _line(ring, minimum=4)
        if ring[0] != ring[-1]:
            raise ValueError("Cada anillo del polígono debe estar cerrado")


def validate_coordinates(kind: str, coords: Any) -> None:
    if kind == "POINT":
        _position(coords)
    elif kind == "LINESTRING":
        _line(coords)
    elif kind == "POLYGON":
        _polygon(coords)
    else:
        if not isinstance(coords, list) or not coords:
            raise ValueError("Un multipolígono necesita al menos un polígono")
        for polygon in coords:
            _polygon(polygon)


@cache
def geometry_schema(kind: str) -> type[BaseModel]:
    """Modelo pydantic de la geometría GeoJSON de un módulo (POINT, POLYGON...)."""
    name = GEOJSON_NAMES[kind]

    class Geometry(BaseModel):
        model_config = ConfigDict(extra="forbid")
        type: Literal[name]  # type: ignore[valid-type]
        coordinates: list[Any]

        @model_validator(mode="after")
        def _check(self) -> "Geometry":
            validate_coordinates(kind, self.coordinates)
            return self

    Geometry.__name__ = Geometry.__qualname__ = f"{name}Geometry"
    return Geometry
