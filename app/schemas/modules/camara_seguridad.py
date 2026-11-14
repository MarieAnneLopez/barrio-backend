"""Módulo 3 · Sistemas de Cámaras de Seguridad (§11.3): solo metadatos y ubicación, nunca video."""

from datetime import date
from typing import Literal

from pydantic import Field

from app.schemas.crud import AuditIn
from app.schemas.modules.fields import Corto, PointGeometry


class CamaraSeguridadCreate(AuditIn):
    codigo: str = Field(min_length=2, max_length=40)
    tipo: Literal["policial", "comunitaria", "privada"]
    operador: Corto
    estado: Literal["activa", "inactiva", "mantenimiento"] | None = None
    fecha_instalacion: date | None = None
    geometry: PointGeometry  # type: ignore[valid-type]
