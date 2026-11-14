"""Módulo 11 · Información de la Localidad 🏛️ (ficha de Kennedy) (slug igual al del frontend: categoryConfig.ts)."""

from app.models import LocalidadKennedy
from app.modules.spec import ModuleSpec
from app.schemas.modules.localidad_kennedy import LocalidadKennedyCreate

SPEC = ModuleSpec(
    slug="localidad",
    model=LocalidadKennedy,
    create_schema=LocalidadKennedyCreate,
    search_fields=("nombre_localidad", "historia", "retos"),
    filter_fields=("verified",),
    sort_fields=("id", "nombre_localidad"),
    within_tintal=False,
)
