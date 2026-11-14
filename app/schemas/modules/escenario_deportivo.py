"""Módulo 2 · Escenarios Deportivos (§11.3), geometría POLYGON."""

from typing import Literal

from pydantic import Field

from app.schemas.crud import AuditIn
from app.schemas.modules.fields import Corto, Horario, Nombre, PolygonGeometry


class EscenarioDeportivoCreate(AuditIn):
    nombre: Nombre
    deportes: str = Field(min_length=2, max_length=300)
    superficie: Corto
    iluminacion: bool | None = None
    horario: Horario
    acceso: Literal["libre", "restringido", "pago"] | None = None
    geometry: PolygonGeometry  # type: ignore[valid-type]
