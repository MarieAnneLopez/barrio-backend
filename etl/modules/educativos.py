"""OSM → Módulo 1 · Centros Educativos.

Nunca se inventa el carácter: público/privado explícito (operator:type) queda
verificado; "IED" (Institución Educativa Distrital) se infiere público pero
"por verificar"; lo demás se omite y se reporta.
"""

import re
from typing import Any

from etl.tintal_config import osm_url

SELECTORS = ['nwr["amenity"~"^(school|kindergarten|college|university)$"]']
OPERATOR_TYPE = {"public": "publico", "government": "publico", "private": "privado"}
IED = re.compile(r"\bI\.?\s?E\.?\s?D\.?\b", re.IGNORECASE)


def _tipo(amenity: str, name: str) -> str:
    if amenity == "kindergarten":
        return "jardin"
    if amenity == "school" or name.lower().startswith(("colegio", "gimnasio", "liceo")):
        return "colegio"
    return "universidad"


def _caracter(tags: dict[str, str], name: str) -> tuple[str | None, bool]:
    explicit = OPERATOR_TYPE.get(tags.get("operator:type", ""))
    if explicit:
        return explicit, True
    if IED.search(name):
        return "publico", False
    return None, False


def map_school(element: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    """Feature GeoJSON listo para la semilla, o (None, motivo de la omisión)."""
    tags = element.get("tags") or {}
    name = (tags.get("name") or "").strip()
    if not name:
        return None, "sin nombre"
    caracter, verified = _caracter(tags, name)
    if caracter is None:
        return None, "carácter público/privado desconocido"
    center = element.get("center") or {"lat": element.get("lat"), "lon": element.get("lon")}
    street = " ".join(p for p in (tags.get("addr:street"), tags.get("addr:housenumber")) if p)
    properties = {
        "nombre": name,
        "tipo": _tipo(tags.get("amenity", ""), name),
        "caracter": caracter,
        "direccion": street or None,
        "telefono": tags.get("phone") or tags.get("contact:phone"),
        "source_type": "osm",
        "source_ref": osm_url(element["type"], element["id"]),
        "verified": verified,
    }
    geometry = {"type": "Point", "coordinates": [center["lon"], center["lat"]]}
    return {"type": "Feature", "properties": properties, "geometry": geometry}, None
