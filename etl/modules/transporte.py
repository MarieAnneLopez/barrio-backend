"""OSM → Módulo 7 · Estaciones del Sistema de Transporte (TransMilenio y SITP).

Troncal: estación con red u operador TransMilenio. Alimentador: la red, el nombre
o las rutas lo dicen. El resto de paraderos con nombre es SITP zonal.
"""

from typing import Any

from etl.modules.common import Mapped, Props, address, name_of, tags_of, trace
from etl.tintal_config import layer_query

SLUG = "estaciones-transporte"
GEOMETRY = "point"
SELECTORS = ['nwr["public_transport"~"^(station|platform)$"]', 'node["highway"="bus_stop"]']
ORDER = {"station": 0, "platform": 1}
GENERIC = {"sitp", "paradero", "parada"}
ROUTES_OUT = '->.s;rel(bn.s)["route"="bus"];out body'


def _tipo(tags: dict[str, str], name: str) -> str:
    text = " ".join((tags.get("network", ""), tags.get("operator", ""), name)).lower()
    if "alimentador" in text:
        return "alimentador"
    if "transmilenio" in text and (tags.get("public_transport") == "station"
                                   or name.lower().startswith("portal")):
        return "troncal"
    return "sitp"


def map_element(element: dict[str, Any]) -> Mapped:
    tags = tags_of(element)
    name = name_of(tags)
    if not name or name.lower() in GENERIC:
        return None, "paradero sin nombre propio"
    routes = sorted(set(element.get("_routes", [])) | set(filter(None, (
        r.strip() for r in (tags.get("route_ref") or "").split(";")))))
    lineas = ", ".join(routes)[:500] or None
    return {"nombre": name, "tipo": _tipo(tags, name), "lineas": lineas,
            "direccion": address(tags), "_rank": ORDER.get(tags.get("public_transport", ""), 2),
            **trace(element)}, None


def enrich(client: Any, elements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Agrega a cada paradero las rutas (relaciones route=bus) que lo usan."""
    query = layer_query(SELECTORS).replace(";out geom;", ROUTES_OUT + ";")
    served: dict[tuple[str, int], set[str]] = {}
    for rel in client.query(query)["elements"]:
        ref = (rel.get("tags") or {}).get("ref")
        for m in rel.get("members", []) if ref else []:
            served.setdefault((m["type"], m["ref"]), set()).add(ref)
    for e in elements:
        e["_routes"] = sorted(served.get((e["type"], e["id"]), set()))
    return elements


def finalize(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Una entrada por (nombre, tipo): la estación gana a sus plataformas y paraderos."""
    best: dict[tuple[str, str], dict[str, Any]] = {}
    for f in features:
        p: Props = f["properties"]
        key = (p["nombre"].lower(), p["tipo"])
        if key not in best or p["_rank"] < best[key]["properties"]["_rank"]:
            best[key] = f
    for f in best.values():
        f["properties"].pop("_rank")
    return list(best.values())
