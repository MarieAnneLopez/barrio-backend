"""Módulo 10 · Datos sobre Robos 🚨 (agregados y anonimizados) (slug igual al del frontend: categoryConfig.ts)."""

from app.models import Robo
from app.modules.spec import ModuleSpec
from app.schemas.modules.robo import RoboCreate

SPEC = ModuleSpec(
    slug="robos",
    model=Robo,
    create_schema=RoboCreate,
    search_fields=("modalidad", "fuente"),
    filter_fields=("modalidad", "franja_horaria", "fecha", "verified"),
    sort_fields=("id", "fecha", "cantidad", "modalidad"),
)
