"""Escritura determinista de GeoJSON (RFC 7946) en seed/: mismo dato, mismo archivo."""

import json
from pathlib import Path
from typing import Any


def _sort_key(f: dict[str, Any]) -> str:
    """Orden estable: id OSM o, en datos abiertos, la referencia de la fuente."""
    props = f["properties"]
    return str(props.get("osm_id") or props.get("source_ref") or "")


def feature(geometry: dict[str, Any], properties: dict[str, Any]) -> dict[str, Any]:
    return {"type": "Feature", "properties": properties, "geometry": geometry}


def write_geojson(path: Path, data: dict[str, Any], pretty: bool = False) -> None:
    """Escribe con orden estable de features y salto final."""
    if data.get("type") == "FeatureCollection":
        data = {
            **data,
            "features": sorted(data["features"], key=_sort_key),
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=2 if pretty else None,
                      separators=None if pretty else (",", ":"))
    # newline="\n": mismo archivo en Windows y Linux (Python traduce \n a os.linesep).
    path.write_text(text + "\n", encoding="utf-8", newline="\n")
