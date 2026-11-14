"""Carga seed/modules/<slug>.geojson en PostGIS, idempotente por source_ref.

Uso (desde barrio-backend/): python -m etl.load_seed
Cada registro se valida con el mismo esquema de la API y debe caer dentro
del polígono de El Tintal; lo demás se rechaza y se reporta.
"""

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from sqlalchemy import Engine, delete, text
from sqlalchemy.orm import Session

from app.core.database import get_engine
from app.modules.registry import MODULES
from app.modules.spec import ModuleSpec
from app.repositories.base_geo_repo import BaseCrudRepository

SEED = Path(__file__).resolve().parent.parent / "seed"
WITHIN = text("SELECT ST_Within(ST_GeomFromGeoJSON(:g), ST_GeomFromGeoJSON(:area))")


def _area(seed_dir: Path) -> str:
    polygon = json.loads((seed_dir / "el_tintal_polygon.geojson").read_text(encoding="utf-8"))
    return json.dumps(polygon["geometry"])


def load_module(session: Session, spec: ModuleSpec, seed_dir: Path = SEED) -> dict[str, Any]:
    path = seed_dir / "modules" / f"{spec.slug}.geojson"
    if not path.exists():
        return {"loaded": 0, "rejected": []}
    features = json.loads(path.read_text(encoding="utf-8"))["features"]
    area = _area(seed_dir)
    valid, rejected = [], []
    for feature in features:
        props = {k: v for k, v in feature["properties"].items() if k != "osm_id"}
        try:
            payload = spec.create_schema.model_validate({**props, "geometry": feature["geometry"]})
        except ValidationError as exc:
            rejected.append({"source_ref": props.get("source_ref"), "reason": str(exc.errors()[0]["msg"])})
            continue
        inside = session.execute(WITHIN, {"g": json.dumps(feature["geometry"]), "area": area}).scalar()
        if not inside:
            rejected.append({"source_ref": props.get("source_ref"), "reason": "fuera de El Tintal"})
            continue
        valid.append(payload)
    refs = [p.source_ref for p in valid if p.source_ref]
    session.execute(delete(spec.model).where(spec.model.source_ref.in_(refs)))  # type: ignore[attr-defined]
    session.commit()
    repo = BaseCrudRepository(session, spec.model)
    for payload in valid:
        repo.create(payload.model_dump(exclude={"geometry"}), payload.model_dump()["geometry"])
    return {"loaded": len(valid), "rejected": rejected}


def run(engine: Engine, seed_dir: Path = SEED) -> dict[str, Any]:
    with Session(engine) as session:
        return {spec.slug: load_module(session, spec, seed_dir) for spec in MODULES}


if __name__ == "__main__":
    print(run(get_engine()))
