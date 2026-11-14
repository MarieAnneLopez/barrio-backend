"""Módulo 4 · Zonas Verdes 🌳 (slug igual al del frontend: categoryConfig.ts)."""

from app.models import ZonaVerde
from app.modules.spec import ModuleSpec
from app.schemas.modules.zona_verde import ZonaVerdeCreate

SPEC = ModuleSpec(
    slug="zonas-verdes",
    model=ZonaVerde,
    create_schema=ZonaVerdeCreate,
    search_fields=("nombre",),
    filter_fields=("tipo", "arborizacion", "estado", "verified"),
    sort_fields=("id", "nombre", "area_m2"),
)
