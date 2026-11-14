"""Tipos de campo compartidos por los esquemas de los 14 módulos (§11.3)."""

from typing import Annotated

from pydantic import Field

from app.schemas.geojson import geometry_schema

PHONE = r"^[0-9 +()\-]{7,30}$"

Nombre = Annotated[str, Field(min_length=2, max_length=200)]
Direccion = Annotated[str | None, Field(None, max_length=200)]
Horario = Annotated[str | None, Field(None, max_length=120)]
Telefono = Annotated[str | None, Field(None, max_length=30, pattern=PHONE)]
TextoLargo = Annotated[str | None, Field(None, max_length=500)]
Corto = Annotated[str | None, Field(None, max_length=120)]

PointGeometry = geometry_schema("POINT")
PolygonGeometry = geometry_schema("POLYGON")
LineGeometry = geometry_schema("LINESTRING")
MultiPolygonGeometry = geometry_schema("MULTIPOLYGON")
