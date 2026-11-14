"""Módulo 7 · Estaciones del Sistema de Transporte (§11.3)."""

from typing import Literal

from app.schemas.crud import AuditIn
from app.schemas.modules.fields import Direccion, Nombre, PointGeometry, TextoLargo


class EstacionTransporteCreate(AuditIn):
    nombre: Nombre
    tipo: Literal["troncal", "alimentador", "sitp"]
    lineas: TextoLargo
    direccion: Direccion
    geometry: PointGeometry  # type: ignore[valid-type]
