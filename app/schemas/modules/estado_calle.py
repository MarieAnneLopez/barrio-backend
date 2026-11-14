"""Módulo 6 · Estado de Calles (§11.3), geometría LINESTRING.

estado es opcional ("por verificar"): ninguna fuente abierta da la clase por tramo (D51).
"""

from datetime import date
from typing import Literal

from pydantic import Field

from app.schemas.crud import AuditIn
from app.schemas.modules.fields import LineGeometry, Nombre


class EstadoCalleCreate(AuditIn):
    nombre_via: Nombre
    tipo_via: str | None = Field(None, max_length=40)
    material: str | None = Field(None, max_length=40)
    estado: Literal["bueno", "regular", "malo"] | None = None
    ultima_intervencion: date | None = None
    reportes_ciudadanos: int | None = Field(None, ge=0)
    geometry: LineGeometry  # type: ignore[valid-type]
