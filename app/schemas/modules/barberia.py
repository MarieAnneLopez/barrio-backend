"""Módulo 14 · Barberías (§11.3). La calificación promedio la calcula H18 desde las reseñas."""

from app.schemas.crud import AuditIn
from app.schemas.modules.fields import Direccion, Horario, Nombre, PointGeometry, TextoLargo


class BarberiaCreate(AuditIn):
    nombre: Nombre
    direccion: Direccion
    horario: Horario
    servicios: TextoLargo
    geometry: PointGeometry  # type: ignore[valid-type]
