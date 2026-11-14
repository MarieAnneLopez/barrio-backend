"""Módulo 14 · Barberías ✂️ (slug igual al del frontend: categoryConfig.ts)."""

from app.models import Barberia
from app.modules.spec import ModuleSpec
from app.schemas.modules.barberia import BarberiaCreate

SPEC = ModuleSpec(
    slug="barberias",
    model=Barberia,
    create_schema=BarberiaCreate,
    search_fields=("nombre", "servicios", "direccion"),
    filter_fields=("verified",),
    sort_fields=("id", "nombre"),
)
