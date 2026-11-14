"""Entorno de Alembic: URL desde la configuración y metadata de los modelos."""

from logging.config import fileConfig
from typing import Any

from alembic import context
from sqlalchemy import Engine

from app.core.config import get_settings
from app.core.database import build_engine
from app.models.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_object(obj: Any, name: str | None, type_: str, reflected: bool, compare_to: Any) -> bool:
    """Ignora tablas ajenas a los modelos (tiger, topology, spatial_ref_sys de PostGIS)."""
    if type_ == "table" and reflected and compare_to is None:
        return False
    return True


def _engine() -> Engine:
    return build_engine(get_settings())


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
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
