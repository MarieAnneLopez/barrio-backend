"""Módulo 3 · Sistemas de Cámaras de Seguridad 📹 (slug igual al del frontend: categoryConfig.ts)."""

from app.models import CamaraSeguridad
from app.modules.spec import ModuleSpec
from app.schemas.modules.camara_seguridad import CamaraSeguridadCreate

SPEC = ModuleSpec(
    slug="camaras-seguridad",
    model=CamaraSeguridad,
    create_schema=CamaraSeguridadCreate,
    search_fields=("codigo", "operador"),
    filter_fields=("tipo", "estado", "verified"),
    sort_fields=("id", "codigo", "tipo"),
)
