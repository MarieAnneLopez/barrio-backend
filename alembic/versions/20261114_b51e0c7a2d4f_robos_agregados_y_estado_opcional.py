"""robos agregados y estado de calles opcional (D51)

Revision ID: b51e0c7a2d4f
Revises: 9c91ab6b7857
Create Date: 2026-11-14 07:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'b51e0c7a2d4f'
down_revision: str | None = '9c91ab6b7857'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('robos', sa.Column('cantidad', sa.Integer(), nullable=True))
    op.create_check_constraint('ck_robos_cantidad', 'robos', 'cantidad >= 0')
    op.alter_column('robos', 'franja_horaria', existing_type=sa.String(length=20), nullable=True)
    op.alter_column('estado_calles', 'estado', existing_type=sa.String(length=20), nullable=True)


def downgrade() -> None:
    op.execute("DELETE FROM estado_calles WHERE estado IS NULL")
    op.alter_column('estado_calles', 'estado', existing_type=sa.String(length=20), nullable=False)
    op.execute("DELETE FROM robos WHERE franja_horaria IS NULL")
    op.alter_column('robos', 'franja_horaria', existing_type=sa.String(length=20), nullable=False)
    op.drop_constraint('ck_robos_cantidad', 'robos', type_='check')
    op.drop_column('robos', 'cantidad')
