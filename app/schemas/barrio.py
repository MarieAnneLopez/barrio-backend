"""Contrato de /api/v1/barrio/poligono: GeoJSON Feature (RFC 7946) con trazabilidad."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class BarrioProperties(BaseModel):
    nombre: str
    localidad: str
    ciudad: str
    definicion: str = Field(description="Unidades oficiales que forman el polígono")
    source_type: Literal["osm", "datos_abiertos", "seed"]
    source_ref: list[str]
    verified: bool
    license: str
    osm_timestamp: str | None
    area_km2: float
    centroid: tuple[float, float] = Field(description="[lon, lat]")


class BarrioPolygon(BaseModel):
    type: Literal["Feature"]
    bbox: tuple[float, float, float, float] = Field(description="[oeste, sur, este, norte]")
    geometry: dict[str, Any]
    properties: BarrioProperties
