"""Arranque de producción: migra y publica las semillas en una transacción de Postgres."""
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_engine
from app.modules.registry import MODULES
from etl import admin, load_fotos, load_historia, load_seed, sync_places
from etl.seed_manifest import LOCK

ROOT = Path(__file__).resolve().parents[1]


def empty_modules(engine: Engine) -> list[str]:
    with Session(engine) as session:
        return [s.slug for s in MODULES if session.scalar(select(s.model.id).limit(1)) is None]


def is_empty(engine: Engine) -> bool:
    return len(empty_modules(engine)) == len(MODULES)


def has_places(session: Session) -> bool:
    return any(session.scalar(select(s.model.id).limit(1)) is not None for s in MODULES)


def modules(session: Session, seed: Path, forced: set[str], *, adopt: bool) -> dict[str, Any] | str:
    changes = {}
    for spec in MODULES:
        result = load_seed.load_module(session, spec, seed, adopt=adopt, force=spec.slug in forced)
        if result["changed"]:
            if result["rejected"]:
                raise ValueError(f"{spec.slug}: {len(result['rejected'])} registros rechazados")
            changes[spec.slug] = result
    return changes or "ya cargadas"


def load_missing(engine: Engine, forced: set[str] | None = None) -> dict[str, Any] | str:
    with Session(engine) as session, session.begin():
        session.execute(LOCK)
        return modules(session, get_settings().seed_dir, forced or set(), adopt=has_places(session))


def main(engine: Engine | None = None) -> dict[str, object]:
    settings = get_settings()
    admin.check(settings)
    seed = settings.seed_dir
    forced = {s.strip() for s in settings.reseed_modules.split(",") if s.strip()}
    with (engine or get_engine()).begin() as conn:
        conn.execute(LOCK)
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        config = Config(str(ROOT / "alembic.ini"))
        config.attributes["connection"] = conn
        command.upgrade(config, "head")
        with Session(conn) as session, session.begin():
            adopt = has_places(session)
            photos = [p for p in (seed / "fotos.json", seed / "fotos_mapillary.json") if p.is_file()]
            steps = {"semillas": modules(session, seed, forced, adopt=adopt),
                     "lugares": sync_places.retire(session, seed),
                     "historia": load_historia.apply(session, seed / "historia.json"),
                     "fotos": load_fotos.apply(session, photos, adopt=adopt)}
        steps["admin"] = admin.run(conn, settings)
    for name, result in steps.items():
        print(f"[bootstrap] {name}: {result if name != 'semillas' or isinstance(result, str) else 'cargadas'}")
    return steps


if __name__ == "__main__":
    main()
