"""Módulo 7 · Estaciones del Sistema de Transporte 🚉 (slug igual al del frontend: categoryConfig.ts)."""

from app.models import EstacionTransporte
from app.modules.spec import ModuleSpec
from app.schemas.modules.estacion_transporte import EstacionTransporteCreate

SPEC = ModuleSpec(
    slug="estaciones-transporte",
    model=EstacionTransporte,
    create_schema=EstacionTransporteCreate,
    search_fields=("nombre", "lineas", "direccion"),
    filter_fields=("tipo", "verified"),
    sort_fields=("id", "nombre", "tipo"),
)
