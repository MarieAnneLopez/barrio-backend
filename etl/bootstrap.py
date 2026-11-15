"""Arranque en producción (Render, D62): deja la base lista antes de uvicorn.

Uso: python -m etl.bootstrap && uvicorn app.main:app --host 0.0.0.0 --port $PORT
1. Activa PostGIS (los proveedores gratuitos no siempre la traen activa).
2. Aplica las migraciones de Alembic.
3. Carga las semillas de cada módulo que esté vacío: un reinicio no cambia
   los id (calificaciones y fotos siguen valiendo) y un arranque cortado a
   mitad de la carga se completa en el siguiente.
   RESEED_MODULES=slug1,slug2 fuerza la recarga de esos módulos (uso puntual:
   quitar la variable después, porque recargar cambia sus id).
4. Sincroniza nombres y descripciones y aplica seed/eliminados.json (H35).
5. Recarga la Historia Local y las fotos de Commons (D66), y crea o actualiza
   la cuenta de administración.
Sin red: todo sale de seed/ (los datos reales ya vienen del ETL de desarrollo).
"""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_engine
from app.modules.registry import MODULES
from app.repositories.geo_insights_repository import SqlGeoInsightsRepository
from etl import admin, load_fotos, load_historia, load_seed, sync_places

ROOT = Path(__file__).resolve().parents[1]


def empty_modules(engine: Engine) -> list[str]:
    with Session(engine) as session:
        return [spec.slug for spec in MODULES if SqlGeoInsightsRepository(session, spec.model).counts()[0] == 0]


def is_empty(engine: Engine) -> bool:
    return len(empty_modules(engine)) == len(MODULES)


def load_missing(engine: Engine, forced: set[str] | None = None) -> dict[str, object] | str:
    missing = set(empty_modules(engine)) | (forced or set())
    if not missing:
        return "ya cargadas"
    with Session(engine) as session:
        return {spec.slug: load_seed.load_module(session, spec) for spec in MODULES if spec.slug in missing}


def main(engine: Engine | None = None) -> dict[str, object]:
    admin.check(get_settings())  # una clave inválida detiene el arranque antes de tocar la base
    engine = engine or get_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    forced = {s.strip() for s in get_settings().reseed_modules.split(",") if s.strip()}
    steps: dict[str, object] = {"semillas": load_missing(engine, forced)}
    steps["lugares"] = sync_places.run(engine)  # H35: nombres, descripciones y eliminados
    steps["historia"] = load_historia.run(engine)
    steps["fotos"] = load_fotos.run(engine)
    steps["admin"] = admin.run(engine)
    for name, result in steps.items():
        print(f"[bootstrap] {name}: {result if name != 'semillas' or isinstance(result, str) else 'cargadas'}")
    return steps


if __name__ == "__main__":
    main()
