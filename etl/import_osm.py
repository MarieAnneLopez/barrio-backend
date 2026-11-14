"""ETL OSM de El Tintal: polígono (UPZ 78 + 79) y capas base recortadas.

Uso (desde barrio-backend/, con PostGIS arriba):
    python -m etl.import_osm
Idempotente: reescribe seed/el_tintal_polygon.geojson y seed/base/*.geojson.
"""

from pathlib import Path
from typing import Any

from sqlalchemy import Connection, Engine

from app.core.database import get_engine
from etl.osm_geometry import relation_outer_wkt, way_wkt
from etl.overpass import OverpassClient
from etl.postgis_ops import build_area, clip, load_clip_area
from etl.seed_writer import feature, write_geojson
from etl.tintal_config import (
    CENTROID_LAT, CENTROID_LON, KIND_KEYS, LAYERS, OSM_LICENSE, UPZ_RELATIONS,
    layer_query, osm_url, polygon_query,
)

SEED_DIR = Path(__file__).resolve().parent.parent / "seed"


def import_polygon(client: OverpassClient, conn: Connection, seed_dir: Path) -> dict[str, Any]:
    data = client.query(polygon_query())
    relations = [e for e in data["elements"] if e.get("type") == "relation"]
    found = {r["id"] for r in relations}
    if found != set(UPZ_RELATIONS):
        raise ValueError(f"Relaciones esperadas {sorted(UPZ_RELATIONS)}, recibidas {sorted(found)}")
    area = build_area(conn, [relation_outer_wkt(r) for r in relations])
    lon, lat = area.centroid
    if not (area.valid and CENTROID_LAT[0] <= lat <= CENTROID_LAT[1]
            and CENTROID_LON[0] <= lon <= CENTROID_LON[1]):
        raise ValueError(f"Polígono fuera de rango o inválido: centroide {lat:.5f}, {lon:.5f}")
    properties = {
        "nombre": "El Tintal", "localidad": "Kennedy", "ciudad": "Bogotá D.C.",
        "definicion": " + ".join(UPZ_RELATIONS.values()),
        "source_type": "osm",
        "source_ref": [osm_url("relation", i) for i in sorted(UPZ_RELATIONS)],
        "verified": True, "license": OSM_LICENSE,
        "osm_timestamp": data.get("osm3s", {}).get("timestamp_osm_base"),
        "area_km2": round(area.area_km2, 4),
        "centroid": [round(lon, 6), round(lat, 6)],
    }
    polygon = {**feature(area.geometry, properties), "bbox": [round(v, 6) for v in area.bbox]}
    write_geojson(seed_dir / "el_tintal_polygon.geojson", polygon, pretty=True)
    return polygon


def _layer_feature(layer: str, element: dict[str, Any], conn: Connection) -> dict | None:
    tags = element.get("tags") or {}
    is_relation = element["type"] == "relation"
    wkt = relation_outer_wkt(element) if is_relation else way_wkt(element)
    geometry = clip(conn, wkt, is_relation)
    if geometry is None:
        return None
    kind = next((tags[k] for k in KIND_KEYS[layer] if k in tags), None)
    props = {"osm_id": f"{element['type']}/{element['id']}", "name": tags.get("name"),
             "kind": kind, "source_type": "osm",
             "source_ref": osm_url(element["type"], element["id"]), "verified": True}
    if layer == "edificios":
        props |= {"levels": tags.get("building:levels"), "height": tags.get("height")}
    return feature(geometry, props)


def import_layers(client: OverpassClient, conn: Connection, seed_dir: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for layer, selectors in LAYERS.items():
        elements = client.query(layer_query(selectors))["elements"]
        features = [f for e in elements if (f := _layer_feature(layer, e, conn))]
        collection = {"type": "FeatureCollection", "name": layer, "license": OSM_LICENSE,
                      "features": features}
        write_geojson(seed_dir / "base" / f"{layer}.geojson", collection)
        counts[layer] = len(features)
    return counts


def run(client: OverpassClient, engine: Engine, seed_dir: Path = SEED_DIR) -> dict[str, Any]:
    with engine.begin() as conn:
        polygon = import_polygon(client, conn, seed_dir)
        load_clip_area(conn, polygon["geometry"])
        counts = import_layers(client, conn, seed_dir)
    return {"polygon": polygon["properties"], "bbox": polygon["bbox"], "layers": counts}


if __name__ == "__main__":
    summary = run(OverpassClient(), get_engine())
    print(summary)
