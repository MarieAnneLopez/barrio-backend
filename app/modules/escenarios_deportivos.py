"""Módulo 2 · Escenarios Deportivos ⚽ (slug igual al del frontend: categoryConfig.ts)."""

from app.models import EscenarioDeportivo
from app.modules.spec import ModuleSpec
from app.schemas.modules.escenario_deportivo import EscenarioDeportivoCreate

SPEC = ModuleSpec(
    slug="escenarios-deportivos",
    model=EscenarioDeportivo,
    create_schema=EscenarioDeportivoCreate,
    search_fields=("nombre", "deportes"),
    filter_fields=("acceso", "iluminacion", "verified"),
    sort_fields=("id", "nombre"),
)
