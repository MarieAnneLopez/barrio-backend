"""Módulo 1 · Centros Educativos 🎓 (slug igual al del frontend: categoryConfig.ts)."""

from app.models import CentroEducativo
from app.modules.spec import ModuleSpec
from app.schemas.modules.centro_educativo import CentroEducativoCreate

SPEC = ModuleSpec(
    slug="centros-educativos",
    model=CentroEducativo,
    create_schema=CentroEducativoCreate,
    search_fields=("nombre", "direccion", "niveles"),
    filter_fields=("tipo", "caracter", "verified"),
    sort_fields=("id", "nombre", "tipo"),
)
