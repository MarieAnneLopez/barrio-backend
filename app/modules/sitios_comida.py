"""Módulo 8 · Sitios de Comida 👨‍🍳 (slug igual al del frontend: categoryConfig.ts)."""

from app.models import SitioComida
from app.modules.spec import ModuleSpec
from app.schemas.modules.sitio_comida import SitioComidaCreate

SPEC = ModuleSpec(
    slug="sitios-comida",
    model=SitioComida,
    create_schema=SitioComidaCreate,
    search_fields=("nombre", "especialidad", "direccion"),
    filter_fields=("rango_precios", "verified"),
    sort_fields=("id", "nombre"),
)
