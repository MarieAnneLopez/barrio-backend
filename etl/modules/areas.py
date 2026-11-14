"""OSM → Módulos 2 · Escenarios Deportivos y 4 · Zonas Verdes (POLYGON).

Si OSM no da nombre se usa uno descriptivo derivado de las etiquetas y el
registro queda "por verificar" (verified=false); nada se inventa.
"""

from typing import Any

from etl.modules.common import Mapped, hours, name_of, tags_of, trace, translate

SPORTS = {"soccer": "fútbol", "basketball": "baloncesto", "volleyball": "voleibol",
          "tennis": "tenis", "multi": "multideporte", "skateboard": "patinaje",
          "athletics": "atletismo", "running": "atletismo", "fitness": "gimnasio al aire libre",
          "table_tennis": "tenis de mesa", "baseball": "béisbol", "swimming": "natación",
          "roller_skating": "patinaje", "bmx": "BMX", "cycling": "ciclismo", "futsal": "fútbol de salón"}
SURFACES = {"grass": "césped", "artificial_turf": "césped sintético", "asphalt": "asfalto",
            "concrete": "concreto", "sand": "arena", "dirt": "tierra", "paving_stones": "adoquín",
            "tartan": "tartán", "clay": "arcilla", "ground": "tierra", "paved": "pavimento"}
KINDS = {"pitch": "Cancha", "sports_centre": "Centro deportivo", "stadium": "Estadio",
         "track": "Pista"}


def _acceso(tags: dict[str, str]) -> str | None:
    if tags.get("fee") == "yes":
        return "pago"
    if tags.get("access") in ("private", "customers", "permissive", "no"):
        return "restringido"
    if tags.get("access") in ("yes", "public"):
        return "libre"
    return None


def map_sport(element: dict[str, Any]) -> Mapped:
    tags = tags_of(element)
    deportes = translate(tags.get("sport"), SPORTS)
    name = name_of(tags)
    if not name and not deportes:
        return None, "sin nombre ni deporte"
    kind = KINDS.get(tags.get("leisure", ""), "Escenario")
    lit = tags.get("lit")
    return {
        "nombre": name or f"{kind} de {deportes}",
        "deportes": deportes or "por verificar",
        "superficie": translate(tags.get("surface"), SURFACES),
        "iluminacion": {"yes": True, "no": False}.get(lit or ""),
        "horario": hours(tags),
        "acceso": _acceso(tags),
        **trace(element, verified=bool(name and deportes)),
    }, None


def map_green(element: dict[str, Any]) -> Mapped:
    tags = tags_of(element)
    name = name_of(tags)
    tipo = "jardin" if tags.get("leisure") == "garden" else "parque"
    if "alameda" in name.lower():
        tipo = "alameda"
    return {
        "nombre": name or ("Jardín sin nombre en OSM" if tipo == "jardin" else "Parque sin nombre en OSM"),
        "tipo": tipo,
        "arborizacion": None,
        "estado": None,
        **trace(element, verified=bool(name)),
    }, None


class Module:
    """Adaptador al contrato de etl/modules/common.py; MEASURE = medida a calcular en PostGIS."""

    GEOMETRY = "polygon"

    def __init__(self, slug: str, selectors: list[str], mapper: Any, measure: str | None) -> None:
        self.SLUG, self.SELECTORS, self.map_element, self.MEASURE = slug, selectors, mapper, measure


DEPORTIVOS = Module("escenarios-deportivos",
                    ['way["leisure"~"^(pitch|sports_centre|stadium|track)$"]'], map_sport, None)
ZONAS_VERDES = Module("zonas-verdes",
                      ['way["leisure"~"^(park|garden)$"]', 'relation["leisure"="park"]'],
                      map_green, "area_m2")
