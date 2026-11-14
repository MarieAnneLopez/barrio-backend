"""OSM → Módulo 6 · Estado de Calles (LINESTRING).

Geometría, nombre, tipo y material salen de OSM. El estado solo se fija con
la regla publicada por el IDU: afirmado y tierra se reportan como "malo".
Para lo demás no hay fuente abierta con la clase por tramo: queda nulo
("por verificar", D51).
"""

from typing import Any

from etl.modules.common import Mapped, name_of, tags_of, trace, translate

SLUG = "estado-calles"
GEOMETRY = "line"
MEASURE = None
ROADS = "primary|secondary|tertiary|residential|trunk|living_street|unclassified|" \
        "primary_link|secondary_link|tertiary_link|trunk_link|pedestrian"
SELECTORS = [f'way["highway"~"^({ROADS})$"]["name"]']
TIPOS = {"trunk": "troncal", "primary": "arterial principal", "secondary": "arterial secundaria",
         "tertiary": "intermedia", "residential": "local", "living_street": "local",
         "unclassified": "local", "pedestrian": "peatonal"}
MATERIALS = {"asphalt": "asfalto", "concrete": "concreto", "paving_stones": "adoquín",
             "paved": "pavimento", "unpaved": "sin pavimentar", "gravel": "afirmado",
             "compacted": "afirmado", "dirt": "tierra", "ground": "tierra", "sett": "adoquín"}
MALO = {"gravel", "compacted", "dirt", "ground", "unpaved"}


def map_element(element: dict[str, Any]) -> Mapped:
    tags = tags_of(element)
    highway = tags.get("highway", "").removesuffix("_link")
    surface = tags.get("surface")
    return {
        "nombre_via": name_of(tags)[:200],
        "tipo_via": TIPOS.get(highway, highway)[:40] or None,
        "material": (translate(surface, MATERIALS) or "")[:40] or None,
        "estado": "malo" if surface in MALO else None,
        "ultima_intervencion": None,
        "reportes_ciudadanos": None,
        **trace(element),
    }, None
