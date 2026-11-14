"""OSM → Módulo 1 · Centros Educativos.

Nunca se inventa el carácter: público/privado explícito (operator:type) queda
verificado; "IED" (Institución Educativa Distrital) se infiere público pero
"por verificar"; lo demás se omite y se reporta.
"""

import re
from typing import Any

from etl.modules.common import Mapped, address, name_of, phone, tags_of, trace

SLUG = "centros-educativos"
GEOMETRY = "point"
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


def map_element(element: dict[str, Any]) -> Mapped:
    tags = tags_of(element)
    name = name_of(tags)
    if not name:
        return None, "sin nombre"
    caracter, verified = _caracter(tags, name)
    if caracter is None:
        return None, "carácter público/privado desconocido"
    return {
        "nombre": name,
        "tipo": _tipo(tags.get("amenity", ""), name),
        "caracter": caracter,
        "direccion": address(tags),
        "telefono": phone(tags),
        **trace(element, verified),
    }, None
