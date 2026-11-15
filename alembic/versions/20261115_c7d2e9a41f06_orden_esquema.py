"""orden del esquema (D65, aprobado por Marie): nombres claros y sin tablas sin uso

- robos: la restricción `ck_robos_ck_robos_cantidad` (prefijo duplicado por la
  convención de nombres en b51e0c7a2d4f) pasa a `ck_robos_cantidad`.
- datos_catastrales: `matricula_inmobiliaria` pasa a `codigo_lote`, que es lo
  que guarda (LOTCODIGO; la matrícula no es pública, D51), con su UNIQUE.
- faq_items: se retira; las preguntas frecuentes viven en las traducciones del
  frontend y la tabla nunca se usó.

Revision ID: c7d2e9a41f06
Revises: b51e0c7a2d4f
Create Date: 2026-11-15
"""

import sqlalchemy as sa
from alembic import op

revision = "c7d2e9a41f06"
down_revision = "b51e0c7a2d4f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE robos RENAME CONSTRAINT ck_robos_ck_robos_cantidad TO ck_robos_cantidad")
    op.alter_column("datos_catastrales", "matricula_inmobiliaria", new_column_name="codigo_lote")
    op.execute("ALTER TABLE datos_catastrales RENAME CONSTRAINT uq_datos_catastrales_matricula_inmobiliaria "
               "TO uq_datos_catastrales_codigo_lote")
    op.drop_table("faq_items")


def downgrade() -> None:
    op.create_table(
        "faq_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pregunta_es", sa.Text(), nullable=False),
        sa.Column("respuesta_es", sa.Text(), nullable=False),
        sa.Column("pregunta_en", sa.Text(), nullable=False),
        sa.Column("respuesta_en", sa.Text(), nullable=False),
        sa.Column("orden", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_faq_items"),
    )
    op.execute("ALTER TABLE datos_catastrales RENAME CONSTRAINT uq_datos_catastrales_codigo_lote "
               "TO uq_datos_catastrales_matricula_inmobiliaria")
    op.alter_column("datos_catastrales", "codigo_lote", new_column_name="matricula_inmobiliaria")
    op.execute("ALTER TABLE robos RENAME CONSTRAINT ck_robos_cantidad TO ck_robos_ck_robos_cantidad")
