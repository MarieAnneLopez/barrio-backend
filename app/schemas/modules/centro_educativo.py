"""Módulo 1 · Centros Educativos (§11.3): campos mínimos obligatorios y geometría POINT."""

from typing import Literal

from pydantic import Field

from app.schemas.crud import AuditIn
from app.schemas.geojson import geometry_schema

PointGeometry = geometry_schema("POINT")
PHONE = r"^[0-9 +()\-]{7,30}$"


class CentroEducativoCreate(AuditIn):
    nombre: str = Field(min_length=2, max_length=200)
    tipo: Literal["jardin", "colegio", "universidad"]
    caracter: Literal["publico", "privado"]
    direccion: str | None = Field(None, max_length=200)
    jornadas: str | None = Field(None, max_length=200)
    niveles: str | None = Field(None, max_length=300)
    telefono: str | None = Field(None, max_length=30, pattern=PHONE)
    geometry: PointGeometry  # type: ignore[valid-type]
