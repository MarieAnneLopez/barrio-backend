"""Aplica las bajas H35 una sola vez. Los IDs conservan sus fotos y calificaciones."""
import json
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.models.seed_manifest import SeedManifest
from app.modules.registry import MODULES
from etl import load_seed
from etl.seed_manifest import LOCK, digest, save


def retire(session: Session, seed: Path) -> dict[str, int]:
    path = seed / "eliminados.json"
    count = 0
    if path.is_file():
        version = digest([path])
        manifest = session.get(SeedManifest, "eliminados")
        if manifest and manifest.digest == version:
            return {"retirados": 0}
        records = dict(manifest.records) if manifest else {}
        models: dict[str, Any] = {s.slug: s.model for s in MODULES}
        for item in json.loads(path.read_text(encoding="utf-8"))["eliminados"]:
            slug = item["modulo"]
            ref = item["feature"]["properties"]["source_ref"]
            key = json.dumps([slug, ref])
            if key not in records:
                model = models[slug]
                for row in session.scalars(select(model).where(model.source_ref == ref).with_for_update()):
                    if row.publicado:
                        row.publicado = False
                        count += 1
                records[key] = True
        save(session, "eliminados", version, records)
    return {"retirados": count}


def run(engine: Engine, seed: Path = load_seed.SEED) -> dict[str, int]:
    with Session(engine) as session, session.begin():
        session.execute(LOCK)
        return retire(session, seed)
