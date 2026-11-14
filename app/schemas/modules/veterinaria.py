"""Módulo 13 · Veterinarias (§11.3). La calificación promedio la calcula H18 desde las reseñas."""

from app.schemas.crud import AuditIn
from app.schemas.modules.fields import Direccion, Horario, Nombre, PointGeometry, TextoLargo


class VeterinariaCreate(AuditIn):
    nombre: Nombre
    servicios: TextoLargo
    direccion: Direccion
    horario: Horario
    geometry: PointGeometry  # type: ignore[valid-type]
