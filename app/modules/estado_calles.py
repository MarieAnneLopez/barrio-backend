"""Módulo 6 · Estado de Calles 🛣️ (slug igual al del frontend: categoryConfig.ts)."""

from app.models import EstadoCalle
from app.modules.spec import ModuleSpec
from app.schemas.modules.estado_calle import EstadoCalleCreate

SPEC = ModuleSpec(
    slug="estado-calles",
    model=EstadoCalle,
    create_schema=EstadoCalleCreate,
    search_fields=("nombre_via", "material"),
    filter_fields=("estado", "tipo_via", "material", "verified"),
    sort_fields=("id", "nombre_via"),
)
