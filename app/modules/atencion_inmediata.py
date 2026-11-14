"""Módulo 12 · Centros de Atención Inmediata 🚑 (slug igual al del frontend: categoryConfig.ts)."""

from app.models import AtencionInmediata
from app.modules.spec import ModuleSpec
from app.schemas.modules.atencion_inmediata import AtencionInmediataCreate

SPEC = ModuleSpec(
    slug="atencion-inmediata",
    model=AtencionInmediata,
    create_schema=AtencionInmediataCreate,
    search_fields=("nombre", "direccion"),
    filter_fields=("tipo", "verified"),
    sort_fields=("id", "nombre", "tipo"),
)
