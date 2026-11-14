"""Módulo 10 · Datos sobre Robos (§11.3): agregados y anonimizados, nunca casos individuales.

franja_horaria es opcional porque la fuente oficial (Línea 123) agrega por mes (D51).
"""

from datetime import date
from typing import Literal

from pydantic import Field

from app.schemas.crud import AuditIn
from app.schemas.modules.fields import PointGeometry


class RoboCreate(AuditIn):
    fecha: date
    franja_horaria: Literal["madrugada", "manana", "tarde", "noche"] | None = None
    modalidad: str = Field(min_length=2, max_length=60)
    fuente: str = Field(min_length=2, max_length=200)
    cantidad: int | None = Field(None, ge=0)
    geometry: PointGeometry  # type: ignore[valid-type]
