"""fuente sitio_oficial (H35, aprobado por Marie)

Agrega «sitio_oficial» a los tipos de fuente permitidos: el sitio web del propio
establecimiento (p. ej. el directorio del C. C. Tintal Plaza) para lugares que no
están en OpenStreetMap ni en Datos Abiertos. Solo cambia el CHECK de source_type.

Revision ID: 5e1f0b7c2a90
Revises: 43a1653b9e3b
Create Date: 2026-11-15
"""
from collections.abc import Sequence

from alembic import op

revision: str = "5e1f0b7c2a90"
down_revision: str | None = "43a1653b9e3b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("atencion_inmediata", "barberias", "camaras_seguridad", "centros_educativos", "datos_catastrales",
          "escenarios_deportivos", "estaciones_transporte", "estado_calles", "fotos", "historia_hitos",
          "librerias", "localidad_kennedy", "robos", "sitios_comida", "veterinarias", "zonas_verdes")
OLD = "source_type IN ('osm', 'datos_abiertos', 'seed')"
NEW = "source_type IN ('osm', 'datos_abiertos', 'seed', 'sitio_oficial')"


def _swap(condition: str) -> None:
    for table in TABLES:
        name = op.f(f"ck_{table}_source_type")
        op.drop_constraint(name, table, type_="check")
        op.create_check_constraint(name, table, condition)


def upgrade() -> None:
    _swap(NEW)


def downgrade() -> None:
    # Falla si ya hay filas «sitio_oficial»: hay que quitarlas o cambiarlas antes de bajar.
    _swap(OLD)
