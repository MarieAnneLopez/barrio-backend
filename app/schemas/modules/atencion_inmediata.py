"""Módulo 12 · Centros de Atención Inmediata (§11.3)."""

from typing import Literal

from app.schemas.crud import AuditIn
from app.schemas.modules.fields import Direccion, Nombre, PointGeometry, Telefono


class AtencionInmediataCreate(AuditIn):
    nombre: Nombre
    tipo: Literal["cai", "hospital", "urgencias"]
    direccion: Direccion
    telefono_24_7: Telefono
    geometry: PointGeometry  # type: ignore[valid-type]
