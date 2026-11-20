"""Carga módulos por revisión conservando identificadores, bajas y campos editoriales."""
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.core.database import get_engine
from app.models.seed_manifest import SeedManifest
from app.modules.registry import MODULES
from app.modules.spec import ModuleSpec
from etl.place_revision import reconcile
from etl.seed_manifest import LOCK, digest, save

SEED = Path(__file__).resolve().parent.parent / "seed"
INSIDE = text("""SELECT ord FROM jsonb_array_elements(CAST(:geometries AS jsonb))
    WITH ORDINALITY AS shapes(geom, ord)
    WHERE ST_Within(ST_GeomFromGeoJSON(geom), ST_GeomFromGeoJSON(:area))""")


def validate(session: Session, spec: ModuleSpec, path: Path, area_path: Path) -> tuple[list[Any], list[Any]]:
    valid, rejected = [], []
    for feature in json.loads(path.read_text(encoding="utf-8"))["features"]:
        props = {k: v for k, v in feature["properties"].items() if k != "osm_id"}
        try:
            valid.append(spec.create_schema.model_validate({**props, "geometry": feature["geometry"]}))
        except ValidationError as exc:
            rejected.append({"source_ref": props.get("source_ref"), "reason": exc.errors()[0]["msg"]})
    if not spec.within_tintal or not valid:
        return valid, rejected
    polygon = json.loads(area_path.read_text(encoding="utf-8"))["geometry"]
    geometries = [p.model_dump(mode="json")["geometry"] for p in valid]
    inside = set(session.scalars(INSIDE, {"geometries": json.dumps(geometries), "area": json.dumps(polygon)}))
    rejected.extend({"source_ref": p.source_ref, "reason": "fuera de El Tintal"}
                    for index, p in enumerate(valid, 1) if index not in inside)
    return [p for index, p in enumerate(valid, 1) if index in inside], rejected


def load_module(session: Session, spec: ModuleSpec, seed_dir: Path = SEED, *,
                adopt: bool = False, force: bool = False) -> dict[str, Any]:
    path = seed_dir / "modules" / f"{spec.slug}.geojson"
    if not path.is_file():
        return {"loaded": 0, "rejected": [], "changed": False}
    session.execute(LOCK)
    area = seed_dir / "el_tintal_polygon.geojson"
    version = digest([path, area])
    manifest = session.get(SeedManifest, spec.slug)
    if manifest and version == manifest.digest and not force:
        return {**manifest.records["result"], "changed": False}
    valid, rejected = validate(session, spec, path, area)
    previous = manifest.records["items"] if manifest else None
    items = reconcile(session, spec, valid, previous, adopt)
    result = {"loaded": len(valid), "rejected": rejected}
    save(session, spec.slug, version, {"items": items, "result": result})
    return {**result, "changed": True}


def run(engine: Engine, seed_dir: Path = SEED) -> dict[str, Any]:
    with Session(engine) as session, session.begin():
        return {spec.slug: load_module(session, spec, seed_dir) for spec in MODULES}


if __name__ == "__main__":
    print(run(get_engine()))
