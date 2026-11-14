"""ETL OSM → semillas de módulos: seed/modules/<slug>.geojson (+ omitidos con motivo).

Uso (desde barrio-backend/, con PostGIS arriba): python -m etl.import_modules
Cada módulo de etl/modules/ declara selectores Overpass, tipo de geometría y
mapeo (contrato en etl/modules/common.py). Idempotente: reescribe las semillas.
"""

import json
from pathlib import Path
from typing import Any

from sqlalchemy import Connection

from app.core.database import get_engine
from etl.geo_parts import largest_part
from etl.modules import areas, calles, comercio, educativos, transporte
from etl.modules.common import center
from etl.osm_geometry import relation_outer_wkt, way_wkt
from etl.overpass import OverpassClient
from etl.postgis_ops import load_clip_area
from etl.seed_writer import write_geojson
from etl.tintal_config import OSM_LICENSE, layer_query

SEED = Path(__file__).resolve().parent.parent / "seed"
OSM_MODULES: tuple[Any, ...] = (
    educativos, areas.DEPORTIVOS, areas.ZONAS_VERDES, calles, transporte,
    comercio.COMIDA, comercio.LIBRERIAS, comercio.VETERINARIAS, comercio.BARBERIAS,
)


def _geometry(module: Any, element: dict[str, Any], conn: Connection) -> tuple[Any, str | None]:
    if module.GEOMETRY == "point":
        return center(element), None
    is_relation = element["type"] == "relation"
    wkt = relation_outer_wkt(element) if is_relation else way_wkt(element)
    part = largest_part(conn, wkt, module.GEOMETRY, is_relation)
    if part is None:
        return None, "fuera de El Tintal"
    geometry, measure = part
    return (geometry, round(measure, 1)), None


def build(module: Any, elements: list[dict[str, Any]], conn: Connection) -> dict[str, Any]:
    features, skipped = [], []
    for element in elements:
        osm_id = f"{element['type']}/{element['id']}"
        props, reason = module.map_element(element)
        geometry = None
        if props is not None:
            geometry, reason = _geometry(module, element, conn)
        if props is None or geometry is None:
            skipped.append({"osm_id": osm_id, "name": (element.get("tags") or {}).get("name"),
                            "reason": reason})
            continue
        if isinstance(geometry, tuple):
            geometry, measure = geometry
            if getattr(module, "MEASURE", None):
                props[module.MEASURE] = measure
        features.append({"type": "Feature", "properties": {**props, "osm_id": osm_id},
                         "geometry": geometry})
    if hasattr(module, "finalize"):
        features = module.finalize(features)
    return {"type": "FeatureCollection", "name": module.SLUG, "license": OSM_LICENSE,
            "skipped": sorted(skipped, key=lambda s: s["osm_id"]), "features": features}


def import_module(client: OverpassClient, module: Any, conn: Connection,
                  out_dir: Path = SEED / "modules") -> dict[str, int]:
    out = "center tags" if module.GEOMETRY == "point" else "geom"
    elements = client.query(layer_query(module.SELECTORS, out=out))["elements"]
    if hasattr(module, "enrich"):
        elements = module.enrich(client, elements)
    collection = build(module, elements, conn)
    write_geojson(out_dir / f"{module.SLUG}.geojson", collection, pretty=True)
    return {"imported": len(collection["features"]), "skipped": len(collection["skipped"])}


def run(client: OverpassClient, conn: Connection, seed_dir: Path = SEED) -> dict[str, Any]:
    polygon = json.loads((seed_dir / "el_tintal_polygon.geojson").read_text(encoding="utf-8"))
    load_clip_area(conn, polygon["geometry"])
    return {m.SLUG: import_module(client, m, conn, seed_dir / "modules") for m in OSM_MODULES}


if __name__ == "__main__":
    with get_engine().begin() as connection:
        print(run(OverpassClient(), connection))
