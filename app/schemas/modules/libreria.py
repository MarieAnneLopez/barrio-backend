"""Módulo 9 · Librerías (§11.3). La calificación promedio la calcula H18 desde las reseñas."""

from app.schemas.crud import AuditIn
from app.schemas.modules.fields import Corto, Direccion, Horario, Nombre, PointGeometry


class LibreriaCreate(AuditIn):
    nombre: Nombre
    direccion: Direccion
    horario: Horario
    especialidad: Corto
    geometry: PointGeometry  # type: ignore[valid-type]
