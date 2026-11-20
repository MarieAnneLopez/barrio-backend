"""Carga seed/fotos.json (Wikimedia Commons, D66) y seed/fotos_mapillary.json (Mapillary, H35).

Uso (desde barrio-backend/): python -m etl.runner --solo fotos
- Cada foto apunta a su lugar por el source_ref del registro (OpenStreetMap),
  que es igual en desarrollo y en producción; los id no lo son.
- Es idempotente: conserva los IDs y las modificaciones editoriales.
- Una foto cuyo lugar no existe no se carga y se informa en "sin_lugar".
- Se rechaza el archivo entero si una foto no cumple la regla de rutas locales
  o le falta autor, licencia o la página de origen (Commons o Mapillary).
"""

import json
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.models import Foto, SeedManifest
from app.modules.registry import MODULES
from app.schemas.engagement import FotoIn
from etl.seed_manifest import LOCK, digest, save

SEED = Path(__file__).resolve().parent.parent / "seed" / "fotos.json"
SEED_MAPILLARY = SEED.with_name("fotos_mapillary.json")
COMMONS = "https://commons.wikimedia.org/wiki/File:"
MAPILLARY = "https://www.mapillary.com/app/?pKey="
SPECS = {spec.slug: spec for spec in MODULES}


def read(path: Path = SEED) -> list[dict[str, Any]]:
    fotos: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))["fotos"]
    for foto in fotos:
        FotoIn.model_validate({k: foto.get(k) for k in ("url", "alt_text", "alt_text_en", "orden", "autor", "licencia")})
        if foto["modulo"] not in SPECS:
            raise ValueError(f"módulo desconocido: {foto['modulo']}")
        if not (foto["autor"] and foto["licencia"] and foto["source_ref"].startswith((COMMONS, MAPILLARY))):
            raise ValueError(f"{foto['url']}: falta autor, licencia o la página de Commons o Mapillary")
    return fotos


def _place_id(session: Session, foto: dict[str, Any]) -> int | None:
    model: Any = SPECS[foto["modulo"]].model
    return session.scalar(select(model.id).where(model.source_ref == foto["lugar_ref"]))


def apply(session: Session, paths: list[Path], *, adopt: bool = False) -> dict[str, Any]:
    version = digest(paths)
    manifest = session.get(SeedManifest, "fotos")
    if manifest and manifest.digest == version:
        return manifest.records["result"]
    records = dict(manifest.records["items"]) if manifest else {}
    missing: list[str] = []
    loaded = 0
    for path in paths:
        for foto in read(path):
            place = _place_id(session, foto)
            if place is None:
                missing.append(foto["url"])
                continue
            key = json.dumps([foto["modulo"], foto["lugar_ref"], foto["source_ref"]])
            last = records.get(key)
            query = select(Foto).where(Foto.categoria_slug == foto["modulo"], Foto.objeto_id == place,
                                       Foto.source_ref == foto["source_ref"]).with_for_update()
            row = session.scalar(query) if last is None else None
            if last and last["id"] is not None:
                row = session.get(Foto, last["id"], with_for_update=True)
            values = {k: foto.get(k) for k in ("url", "alt_text", "alt_text_en", "orden", "autor", "licencia")}
            if row is None and last is None and not (manifest is None and adopt):
                row = Foto(**values, categoria_slug=foto["modulo"], objeto_id=place,
                           source_type="seed", source_ref=foto["source_ref"], verified=True)
                session.add(row)
                session.flush()
            if row is not None:
                if last:
                    for field, value in values.items():
                        if value != last["fields"][field] and getattr(row, field) == last["fields"][field]:
                            setattr(row, field, value)
                loaded += 1
            records[key] = {"id": row.id if row else None, "fields": values}
    result = {"loaded": loaded, "sin_lugar": missing}
    save(session, "fotos", version, {"items": records, "result": result})
    return result


def run(engine: Engine, path: Path | None = None) -> dict[str, Any]:
    paths = [path] if path else [p for p in (SEED, SEED_MAPILLARY) if p.exists()]
    with Session(engine) as session, session.begin():
        session.execute(LOCK)
        return apply(session, paths)
