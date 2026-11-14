"""Contrato de GET /api/v1/historia: hitos con su fuente y el catálogo de fuentes (D55)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class HitoOut(BaseModel):
    """Un hito de la línea de tiempo; verified=False se muestra «por verificar»."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    anio: int
    orden: int
    titulo: str
    descripcion: str
    source_type: str
    source_ref: str | None
    verified: bool


class FuenteOut(BaseModel):
    url: str
    titulo: str
    entidad: str
    tipo: Literal["oficial", "enciclopedia", "comunitaria"]
    nota: str | None


class HistoriaOut(BaseModel):
    consultado: str
    hitos: list[HitoOut]
    fuentes: list[FuenteOut]
