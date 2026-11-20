"""Manifiestos de las cargas de semillas sin modificar las tablas editoriales."""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "812c0d94e56a"
down_revision = "5e1f0b7c2a90"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("seed_manifests", sa.Column("scope", sa.String(100), primary_key=True),
                    sa.Column("digest", sa.String(64), nullable=False), sa.Column("records", JSONB, nullable=False))


def downgrade() -> None:
    op.drop_table("seed_manifests")
