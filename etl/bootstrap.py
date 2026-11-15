"""Arranque en producción (Render, D62): deja la base lista antes de uvicorn.

Uso: python -m etl.bootstrap && uvicorn app.main:app --host 0.0.0.0 --port $PORT
1. Activa PostGIS (los proveedores gratuitos no siempre la traen activa).
2. Aplica las migraciones de Alembic.
3. Carga las semillas de los 14 módulos solo si la base está vacía: un
   reinicio no cambia los id, así que calificaciones y fotos siguen valiendo.
4. Recarga la Historia Local y crea o actualiza la cuenta de administración.
Sin red: todo sale de seed/ (los datos reales ya vienen del ETL de desarrollo).
"""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, text

from app.core.config import get_settings
from app.core.database import get_engine
from app.modules.registry import MODULES
from app.repositories.geo_insights_repository import SqlGeoInsightsRepository
from etl import admin, load_historia, load_seed

ROOT = Path(__file__).resolve().parents[1]


def is_empty(engine: Engine) -> bool:
    from sqlalchemy.orm import Session

    with Session(engine) as session:
        return all(SqlGeoInsightsRepository(session, spec.model).counts()[0] == 0 for spec in MODULES)


def main(engine: Engine | None = None) -> dict[str, object]:
    admin.check(get_settings())  # una clave inválida detiene el arranque antes de tocar la base
    engine = engine or get_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    steps: dict[str, object] = {"semillas": load_seed.run(engine) if is_empty(engine) else "ya cargadas"}
    steps["historia"] = load_historia.run(engine)
    steps["admin"] = admin.run(engine)
    for name, result in steps.items():
        print(f"[bootstrap] {name}: {result if name != 'semillas' or isinstance(result, str) else 'cargadas'}")
    return steps


if __name__ == "__main__":
    main()
