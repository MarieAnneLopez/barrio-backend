"""Carga seed/historia.json en historia_hitos; reemplaza todos los hitos de la semilla.

Uso (desde barrio-backend/): python -m etl.runner --solo historia
Cada hito debe citar una fuente del catálogo del mismo archivo (D55); si no,
se rechaza todo el archivo para no publicar hitos sin trazabilidad. Un hito
quitado de la semilla (D56) también sale de la base al recargar.
"""

import json
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.models import HistoriaHito, SeedManifest
from etl.seed_manifest import LOCK, digest, save

SEED = Path(__file__).resolve().parent.parent / "seed" / "historia.json"
FIELDS = ("anio", "orden", "titulo", "descripcion", "source_ref", "verified")


def read(path: Path = SEED) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    known = {f["url"] for f in data["fuentes"] if f.get("url")}
    hitos = [{k: h[k] for k in FIELDS} for h in data["hitos"]]
    for hito in hitos:
        refs = set(hito["source_ref"].split(" | "))
        if not refs <= known:
            raise ValueError(f"{hito['anio']} cita fuentes fuera del catálogo: {refs - known}")
    return hitos


def apply(session: Session, path: Path) -> dict[str, int]:
    version = digest([path])
    manifest = session.get(SeedManifest, "historia")
    if manifest and manifest.digest == version:
        return manifest.records["result"]
    previous = dict(manifest.records["items"]) if manifest else {}
    rows = list(session.scalars(select(HistoriaHito).where(HistoriaHito.source_type == "seed").with_for_update()))
    by_id = {row.id: row for row in rows}
    by_year = {row.anio: row for row in rows}
    hitos = read(path)
    records = dict(previous)
    for hito in hitos:
        key = str(hito["anio"])
        last = previous.get(key)
        row = by_id.get(last["id"]) if last else by_year.get(hito["anio"])
        if row is None and last is None:
            row = HistoriaHito(source_type="seed", **hito)
            session.add(row)
            session.flush()
        if row is not None:
            if last:
                for field, value in hito.items():
                    if getattr(row, field) == last["fields"][field]:
                        setattr(row, field, value)
            records[key] = {"id": row.id, "fields": hito}
    years = {h["anio"] for h in hitos}
    for row in rows:
        if row.anio in years:
            continue
        last = previous.get(str(row.anio))
        # Solo salen hitos de una revisión anterior intactos o semillas antiguas sin fuente.
        if (last and all(getattr(row, k) == v for k, v in last["fields"].items())) or row.source_ref is None:
            session.delete(row)
    result = {"loaded": len(hitos), "verified": sum(h["verified"] for h in hitos)}
    save(session, "historia", version, {"items": records, "result": result})
    return result


def run(engine: Engine, path: Path = SEED) -> dict[str, int]:
    with Session(engine) as session, session.begin():
        session.execute(LOCK)
        return apply(session, path)
