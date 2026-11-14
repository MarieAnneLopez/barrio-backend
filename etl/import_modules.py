"""ETL OSM → semillas de módulos: seed/modules/<slug>.geojson (+ omitidos con motivo).

Uso (desde barrio-backend/): python -m etl.import_modules
Cada módulo declara sus selectores Overpass y su función de mapeo.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from etl.modules import educativos
from etl.overpass import OverpassClient
from etl.seed_writer import write_geojson
from etl.tintal_config import OSM_LICENSE, layer_query

Mapper = Callable[[dict[str, Any]], tuple[dict[str, Any] | None, str | None]]
SEED_MODULES = Path(__file__).resolve().parent.parent / "seed" / "modules"

MAPPERS: dict[str, tuple[list[str], Mapper]] = {
    "centros-educativos": (educativos.SELECTORS, educativos.map_school),
}


def import_module(client: OverpassClient, slug: str, out_dir: Path = SEED_MODULES) -> dict[str, int]:
    selectors, mapper = MAPPERS[slug]
    elements = client.query(layer_query(selectors, out="center tags"))["elements"]
    features: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for element in elements:
        feature, reason = mapper(element)
        if feature is not None:
            features.append(feature)
        else:
            skipped.append({"osm_id": f"{element['type']}/{element['id']}",
                            "name": (element.get("tags") or {}).get("name"), "reason": reason})
    for feature in features:
        feature["properties"]["osm_id"] = feature["properties"]["source_ref"].split(".org/")[1]
    collection = {"type": "FeatureCollection", "name": slug, "license": OSM_LICENSE,
                  "skipped": sorted(skipped, key=lambda s: s["osm_id"]), "features": features}
    write_geojson(out_dir / f"{slug}.geojson", collection, pretty=True)
    return {"imported": len(features), "skipped": len(skipped)}


if __name__ == "__main__":
    client = OverpassClient()
    for module in MAPPERS:
        print(module, import_module(client, module))
