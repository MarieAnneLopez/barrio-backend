"""Módulo 5 · Datos Catastrales 🏠 (sin datos personales) (slug igual al del frontend: categoryConfig.ts)."""

from app.models import DatoCatastral
from app.modules.spec import ModuleSpec
from app.schemas.modules.dato_catastral import DatoCatastralCreate

SPEC = ModuleSpec(
    slug="datos-catastrales",
    model=DatoCatastral,
    create_schema=DatoCatastralCreate,
    search_fields=("matricula_inmobiliaria", "direccion"),
    filter_fields=("estrato", "uso", "verified"),
    sort_fields=("id", "matricula_inmobiliaria", "area_lote_m2", "estrato"),
)
