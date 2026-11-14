"""Módulo 13 · Veterinarias 🐾 (slug igual al del frontend: categoryConfig.ts)."""

from app.models import Veterinaria
from app.modules.spec import ModuleSpec
from app.schemas.modules.veterinaria import VeterinariaCreate

SPEC = ModuleSpec(
    slug="veterinarias",
    model=Veterinaria,
    create_schema=VeterinariaCreate,
    search_fields=("nombre", "servicios", "direccion"),
    filter_fields=("verified",),
    sort_fields=("id", "nombre"),
)
