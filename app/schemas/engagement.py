"""Esquemas de calificaciones, fotos, ranking, cercanía y estadísticas (H18)."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

PHOTO_PATH = r"^/assets/photos/[A-Za-z0-9_./\-]+\.(jpg|jpeg|png|webp)$"


class CalificacionIn(BaseModel):
    """Estrellas de 0,0 a 5,0 en pasos de 0,5 (§11.3 punto 5)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    estrellas: Decimal = Field(ge=0, le=5, multiple_of=Decimal("0.5"))
    comentario: str | None = Field(None, max_length=500)
    autor_nombre: str | None = Field(None, max_length=120)


class CalificacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    estrellas: float
    comentario: str | None
    autor_nombre: str | None
    created_at: datetime


class ResumenCalificaciones(BaseModel):
    promedio: float | None
    total: int
    items: list[CalificacionOut]


class RankingItem(BaseModel):
    categoria_slug: str
    objeto_id: int
    nombre: str
    promedio: float
    total: int


class FotoIn(BaseModel):
    """Solo archivos locales del frontend: nunca enlaces externos para imágenes."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    url: str = Field(max_length=500, pattern=PHOTO_PATH)
    alt_text: str = Field(min_length=3, max_length=300)
    orden: int = Field(0, ge=0, le=999)
    autor: str | None = Field(None, max_length=200)
    licencia: str | None = Field(None, max_length=120)
    source_type: Literal["osm", "datos_abiertos", "seed"] = "seed"
    source_ref: str | None = Field(None, max_length=500)
    verified: bool = False


class FotoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    url: str
    alt_text: str
    orden: int
    autor: str | None
    licencia: str | None
    source_type: str
    source_ref: str | None
    verified: bool


class GaleriaItem(FotoOut):
    """Foto de la Galería General con el lugar al que pertenece (D66)."""

    categoria_slug: str
    objeto_id: int
    nombre: str


class Cercano(BaseModel):
    distancia_m: float
    item: dict[str, Any]


class Estadisticas(BaseModel):
    total: int
    verificados: int
    por_verificar: int
    ejemplos: int
    calificados: int
    promedio_estrellas: float | None
