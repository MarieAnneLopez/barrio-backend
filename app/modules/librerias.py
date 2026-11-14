"""Módulo 9 · Librerías 📚 (slug igual al del frontend: categoryConfig.ts)."""

from app.models import Libreria
from app.modules.spec import ModuleSpec
from app.schemas.modules.libreria import LibreriaCreate

SPEC = ModuleSpec(
    slug="librerias",
    model=Libreria,
    create_schema=LibreriaCreate,
    search_fields=("nombre", "especialidad", "direccion"),
    filter_fields=("verified",),
    sort_fields=("id", "nombre"),
)
