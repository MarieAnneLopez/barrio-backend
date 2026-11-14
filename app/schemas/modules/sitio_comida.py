"""Módulo 8 · Sitios de Comida (§11.3). La calificación promedio la calcula H18."""

from typing import Literal

from app.schemas.crud import AuditIn
from app.schemas.modules.fields import Corto, Direccion, Horario, Nombre, PointGeometry


class SitioComidaCreate(AuditIn):
    nombre: Nombre
    especialidad: Corto
    direccion: Direccion
    horario: Horario
    rango_precios: Literal["$", "$$", "$$$"] | None = None
    geometry: PointGeometry  # type: ignore[valid-type]
