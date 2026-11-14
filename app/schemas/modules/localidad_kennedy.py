"""Módulo 11 · Información de la Localidad (§11.3): ficha con MULTIPOLYGON opcional.

bandera_url solo acepta rutas locales (/assets/...): sin enlaces externos para imágenes.
"""

from pydantic import Field

from app.schemas.crud import AuditIn
from app.schemas.modules.fields import MultiPolygonGeometry


class LocalidadKennedyCreate(AuditIn):
    nombre_localidad: str = Field(min_length=2, max_length=120)
    bandera_url: str | None = Field(None, max_length=300, pattern=r"^/[A-Za-z0-9_./\-]+$")
    historia: str | None = Field(None, max_length=8000)
    poblacion: int | None = Field(None, ge=0)
    superficie_km2: float | None = Field(None, ge=0)
    alcaldia_local: str | None = Field(None, max_length=200)
    retos: str | None = Field(None, max_length=8000)
    geometry: MultiPolygonGeometry | None = None  # type: ignore[valid-type]
