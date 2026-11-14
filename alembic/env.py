"""Entorno de Alembic: URL desde la configuración y metadata de los modelos."""

from logging.config import fileConfig
from typing import Any

from alembic import context
from geoalchemy2 import alembic_helpers
from sqlalchemy import Engine

from app.core.config import get_settings
from app.core.database import build_engine
import app.models  # noqa: F401  (registra todas las tablas)
from app.models.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_object(obj: Any, name: str | None, type_: str, reflected: bool, compare_to: Any) -> bool:
    """Ignora tablas ajenas a los modelos (tiger, topology, spatial_ref_sys de PostGIS)."""
    if type_ == "table" and reflected and compare_to is None:
        return False
    return alembic_helpers.include_object(obj, name, type_, reflected, compare_to)


def _engine() -> Engine:
    """Base de get_settings(), o la indicada por las pruebas en config.attributes."""
    database = config.attributes.get("database")
    settings = get_settings()
    if database:
        settings = settings.model_copy(update={"postgres_db": database})
    return build_engine(settings)


def run_migrations_offline() -> None:
    context.configure(
        url=get_settings().database_url.render_as_string(hide_password=False),
        target_metadata=target_metadata,
        include_object=include_object,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = _engine()
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
            # GeoAlchemy2: tablas espaciales con sus índices GIST e imports de tipos.
            process_revision_directives=alembic_helpers.writer,
            render_item=alembic_helpers.render_item,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
