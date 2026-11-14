"""Ayudas comunes a los mapeos OSM → módulo.

Contrato de cada módulo de `etl/modules/`: SLUG, SELECTORS, GEOMETRY
("point" | "polygon" | "line") y `map_element(element) -> (props | None, motivo)`.
Las props no incluyen geometría: el importador la arma (punto) o la recorta
contra El Tintal en PostGIS (polígono, línea).
"""

import re
from typing import Any

from etl.tintal_config import osm_url

Props = dict[str, Any]
Mapped = tuple[Props | None, str | None]
PHONE = re.compile(r"^[0-9 +()\-]{7,30}$")


def tags_of(element: dict[str, Any]) -> dict[str, str]:
    return element.get("tags") or {}


def name_of(tags: dict[str, str]) -> str:
    return (tags.get("name") or "").strip()


def address(tags: dict[str, str]) -> str | None:
    street = " ".join(p for p in (tags.get("addr:street"), tags.get("addr:housenumber")) if p)
    return (street or tags.get("addr:full") or "").strip()[:200] or None


def phone(tags: dict[str, str]) -> str | None:
    """Primer teléfono de OSM si cumple el patrón del esquema; si no, ninguno."""
    raw = (tags.get("phone") or tags.get("contact:phone") or "").split(";")[0].strip()
    return raw if PHONE.match(raw) else None


def hours(tags: dict[str, str]) -> str | None:
    return (tags.get("opening_hours") or "").strip()[:120] or None


def trace(element: dict[str, Any], verified: bool = True) -> Props:
    """Trazabilidad OSM: tipo, URL del elemento y si el dato quedó verificado."""
    return {
        "source_type": "osm",
        "source_ref": osm_url(element["type"], element["id"]),
        "verified": verified,
    }


def center(element: dict[str, Any]) -> dict[str, Any]:
    c = element.get("center") or {"lat": element.get("lat"), "lon": element.get("lon")}
    return {"type": "Point", "coordinates": [c["lon"], c["lat"]]}


def translate(value: str | None, table: dict[str, str]) -> str | None:
    """Valores OSM separados por ';' traducidos; los desconocidos se dejan tal cual."""
    if not value:
        return None
    return ", ".join(table.get(v.strip(), v.strip()) for v in value.split(";") if v.strip())
