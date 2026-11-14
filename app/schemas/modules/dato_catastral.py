"""Módulo 5 · Datos Catastrales (§11.3), geometría POLYGON, sin datos personales.

La matrícula inmobiliaria no es dato abierto: los registros reales guardan aquí
el código de lote catastral de la UAECD (D51). Nunca se guardan propietarios.
"""

from decimal import Decimal

from pydantic import Field

from app.schemas.crud import AuditIn
from app.schemas.modules.fields import Direccion, PolygonGeometry


class DatoCatastralCreate(AuditIn):
    matricula_inmobiliaria: str = Field(min_length=2, max_length=40, pattern=r"^[0-9A-Za-z\-]+$")
    direccion: Direccion
    area_lote_m2: float | None = Field(None, ge=0)
    area_construida_m2: float | None = Field(None, ge=0)
    pisos: int | None = Field(None, ge=0, le=100)
    uso: str | None = Field(None, max_length=40)
    avaluo_cop: Decimal | None = Field(None, ge=0, max_digits=16, decimal_places=0)
    estrato: int | None = Field(None, ge=1, le=6)
    geometry: PolygonGeometry  # type: ignore[valid-type]
