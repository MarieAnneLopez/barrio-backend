"""Escritura determinista de GeoJSON (RFC 7946) en seed/: mismo dato, mismo archivo."""

import json
from pathlib import Path
from typing import Any


def feature(geometry: dict[str, Any], properties: dict[str, Any]) -> dict[str, Any]:
    return {"type": "Feature", "properties": properties, "geometry": geometry}


def write_geojson(path: Path, data: dict[str, Any], pretty: bool = False) -> None:
    """Escribe con orden estable de features (por osm_id) y salto final."""
    if data.get("type") == "FeatureCollection":
        data = {
            **data,
            "features": sorted(data["features"], key=lambda f: f["properties"].get("osm_id", "")),
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=2 if pretty else None,
                      separators=None if pretty else (",", ":"))
    # newline="\n": mismo archivo en Windows y Linux (Python traduce \n a os.linesep).
    path.write_text(text + "\n", encoding="utf-8", newline="\n")
