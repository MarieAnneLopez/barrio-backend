"""Identifica cada fila una vez y conserva las decisiones de edición entre revisiones."""
import json
from collections import Counter, defaultdict
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.base import SRID
from app.modules.spec import ModuleSpec


def reconcile(session: Session, spec: ModuleSpec, valid: list[Any],
              previous: dict[str, Any] | None, adopt: bool) -> dict[str, Any]:
    model = spec.model
    rows = list(session.scalars(select(model).with_for_update()))
    by_ref: dict[str, list[Any]] = defaultdict(list)
    by_id = {}
    for row in rows:
        by_ref[row.source_ref].append(row)
        by_id[row.id] = row
    counts = Counter(p.source_ref for p in valid)
    records = dict(previous or {})
    pending = []
    seen: set[str] = set()
    for payload in valid:
        fields = payload.model_dump(exclude={"geometry"})
        label = fields[spec.label_field]
        ref = fields["source_ref"]
        # Un directorio o «dato de ejemplo» puede ser la fuente de varios lugares.
        key = json.dumps([ref, label], ensure_ascii=False, default=str)
        shared = counts[ref] > 1 or ref is None or key in records
        key = key if shared else json.dumps([ref])
        if key in seen:
            raise ValueError(f"{spec.slug}: identidad repetida en la semilla ({key})")
        seen.add(key)
        last = records.get(key)
        matches = [r for r in by_ref[ref] if not shared or getattr(r, spec.label_field) == label]
        row = by_id.get(last["id"]) if last else (matches[0] if len(matches) == 1 else None)
        editable = {k: fields[k] for k in (spec.label_field, "descripcion_es", "descripcion_en") if k in fields}
        # Algunos módulos (p. ej. robos) usan enums como etiqueta, el manifiesto es JSON.
        editable = json.loads(json.dumps(editable, default=str))
        if row is None and last is None and not (previous is None and adopt) and not matches:
            geometry = payload.model_dump(mode="json")["geometry"]
            row = model(**fields, geom=func.ST_SetSRID(func.ST_GeomFromGeoJSON(json.dumps(geometry)), SRID))
            session.add(row)
        elif row is not None and last:
            for field, value in editable.items():
                if value != last["fields"].get(field) and getattr(row, field) == last["fields"].get(field):
                    setattr(row, field, value)
        pending.append((key, row, editable))
    session.flush()
    for key, row, editable in pending:
        records[key] = {"id": row.id if row else None, "fields": editable}
    return records
