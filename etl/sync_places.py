"""Sincroniza nombre y descripciones de las semillas con la base, y aplica las eliminaciones (H35).

Uso: lo llama etl.bootstrap en cada arranque; es idempotente.
- Busca cada lugar por su source_ref (igual en desarrollo y producción; los id no lo son)
  y actualiza solo nombre, descripcion_es y descripcion_en cuando cambian: no recarga
  módulos ni cambia id, así las calificaciones y fotos siguen valiendo.
- seed/eliminados.json lista los lugares sin información que Marie pidió eliminar
  (copia completa de cada uno); se borran con sus fotos y calificaciones.
"""

import json
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, delete, select
from sqlalchemy.orm import Session

from app.models import Calificacion, Foto
from app.modules.registry import MODULES

SEED = Path(__file__).resolve().parent.parent / "seed"
FIELDS = ("descripcion_es", "descripcion_en")


def _update(session: Session, spec: Any, props: dict[str, Any]) -> bool:
    model: Any = spec.model
    rows = list(session.scalars(select(model).where(model.source_ref == props["source_ref"])))
    if len(rows) > 1:  # misma fuente para varios (datos de ejemplo): se identifican por su nombre
        rows = [r for r in rows if getattr(r, spec.label_field) == props.get(spec.label_field)]
    if len(rows) != 1:
        return False
    row = rows[0]
    wanted = {k: props.get(k) for k in FIELDS}
    if props.get(spec.label_field):
        wanted[spec.label_field] = props[spec.label_field]
    changed = {k: v for k, v in wanted.items() if getattr(row, k) != v}
    for key, value in changed.items():
        setattr(row, key, value)
    return bool(changed)


def _remove(session: Session, slug: str, ref: str) -> bool:
    model: Any = {s.slug: s for s in MODULES}[slug].model
    ids = list(session.scalars(select(model.id).where(model.source_ref == ref)))
    for item_id in ids:
        for extra in (Foto, Calificacion):
            session.execute(delete(extra).where(extra.categoria_slug == slug, extra.objeto_id == item_id))
        session.execute(delete(model).where(model.id == item_id))
    return bool(ids)


def run(engine: Engine, seed: Path = SEED) -> dict[str, int]:
    updated = removed = 0
    with Session(engine) as session:
        for spec in MODULES:
            path = seed / "modules" / f"{spec.slug}.geojson"
            if not path.exists():
                continue
            for feature in json.loads(path.read_text(encoding="utf-8"))["features"]:
                props = feature["properties"]
                if props.get("source_ref") and any(props.get(k) for k in FIELDS):
                    updated += _update(session, spec, props)
        gone = seed / "eliminados.json"
        if gone.exists():
            for item in json.loads(gone.read_text(encoding="utf-8"))["eliminados"]:
                removed += _remove(session, item["modulo"], item["feature"]["properties"]["source_ref"])
        session.commit()
    return {"actualizados": updated, "eliminados": removed}
