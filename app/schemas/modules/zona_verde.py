"""Módulo 4 · Zonas Verdes (§11.3), geometría POLYGON."""

from typing import Literal

from pydantic import Field

from app.schemas.crud import AuditIn
from app.schemas.modules.fields import Nombre, PolygonGeometry

Calidad = Literal["bueno", "regular", "malo"]


class ZonaVerdeCreate(AuditIn):
    nombre: Nombre
    area_m2: float | None = Field(None, ge=0)
    tipo: Literal["parque", "alameda", "jardin"]
    arborizacion: Literal["alta", "media", "baja"] | None = None
    estado: Calidad | None = None
    geometry: PolygonGeometry  # type: ignore[valid-type]
