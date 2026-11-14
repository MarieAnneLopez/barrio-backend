"""Bases de datos de prueba: se crean en el PostGIS de docker compose."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from app.core.config import Settings

BACKEND = Path(__file__).resolve().parents[1]


def _admin_url(settings: Settings):  # noqa: ANN202 (URL de SQLAlchemy)
    return settings.database_url.set(database="postgres")


def ensure_database(name: str) -> None:
    """Crea la base (si falta) con la extensión PostGIS."""
    settings = Settings(postgres_db=name)
    admin = create_engine(_admin_url(settings), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": name})
        if exists.scalar() is None:
            conn.execute(text(f'CREATE DATABASE "{name}"'))
    admin.dispose()
    engine = create_engine(settings.database_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    engine.dispose()


def drop_database(name: str) -> None:
    admin = create_engine(_admin_url(Settings(postgres_db=name)), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
    admin.dispose()


def alembic(direction: str, revision: str, database: str | None = None) -> None:
    """Ejecuta Alembic sobre POSTGRES_DB o sobre `database` si se indica."""
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    config.attributes["database"] = database
    getattr(command, direction)(config, revision)
