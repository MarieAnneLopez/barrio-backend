"""Contrato de POST /api/v1/chat (H22, D59)."""

from datetime import date
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


class ChatIn(BaseModel):
    """Mensaje y contexto que percibe el agente: idioma, página actual y ubicación opcional."""

    model_config = ConfigDict(extra="forbid")
    mensaje: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
    idioma: Literal["es", "en"] = "es"
    ruta: Annotated[str | None, StringConstraints(max_length=200, pattern=r"^/[\w\-/]*$")] = None
    lon: float | None = Field(None, ge=-180, le=180)
    lat: float | None = Field(None, ge=-90, le=90)
    contexto_lugar: Annotated[str | None, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)] = None

    @model_validator(mode="after")
    def _both_coordinates(self) -> Self:
        if (self.lon is None) != (self.lat is None):
            raise ValueError("lon y lat van juntas")
        return self


class AccionOut(BaseModel):
    ruta: str
    etiqueta: str


class DatoOut(BaseModel):
    nombre: str
    categoria_slug: str | None
    objeto_id: int | None
    detalle: str | None


class FuenteOut(BaseModel):
    titulo: str
    url: str
    consultado_en: date


class ChatOut(BaseModel):
    intent: str
    texto: str
    expresion: Literal["idle", "wave", "jump", "alert", "sad"]
    modelo: str
    experto: str | None
    acciones: list[AccionOut]
    sugerencias: list[str]
    datos: list[DatoOut]
    fuentes: list[FuenteOut] = Field(default_factory=list)
    lugar: str | None = None


class ChatEstadoOut(BaseModel):
    """Proveedor externo que recibe los mensajes (H36), para el aviso de privacidad del chat."""

    proveedor: Literal["gemini", "claude"] | None
