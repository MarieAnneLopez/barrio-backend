"""Conversión de elementos OSM (Overpass `out geom`) a WKT en lon/lat (SRID 4326)."""

from typing import Any

# Claves que, en una vía cerrada, siguen describiendo una línea y no un área...
LINEAR_KEYS = ("highway", "railway", "waterway", "barrier")
# ...salvo que el elemento también declare un área: en Bogotá es común mapear
# los conjuntos como landuse=residential + barrier=yes (el cerramiento).
AREA_KEYS = ("landuse", "building", "leisure", "amenity")


def _is_area(tags: dict[str, str]) -> bool:
    if tags.get("area") == "yes" or any(key in tags for key in AREA_KEYS):
        return True
    return not any(key in tags for key in LINEAR_KEYS)


def _coords(points: list[dict[str, float]]) -> str:
    return ",".join(f"{p['lon']} {p['lat']}" for p in points)


def way_wkt(way: dict[str, Any]) -> str:
    """LINESTRING para vías; POLYGON para áreas cerradas (edificios, parques)."""
    points = way.get("geometry") or []
    if len(points) < 2:
        raise ValueError(f"way/{way.get('id')} sin geometría")
    closed = points[0] == points[-1] and len(points) >= 4
    if closed and _is_area(way.get("tags") or {}):
        return f"POLYGON(({_coords(points)}))"
    return f"LINESTRING({_coords(points)})"


def relation_outer_wkt(relation: dict[str, Any]) -> str:
    """Bordes exteriores de una relación como MULTILINESTRING (PostGIS arma el área)."""
    lines = [
        f"({_coords(member['geometry'])})"
        for member in relation.get("members", [])
        if member.get("type") == "way"
        and member.get("role") in ("outer", "")
        and member.get("geometry")
    ]
    if not lines:
        raise ValueError("Relación sin miembros exteriores con geometría")
    return f"MULTILINESTRING({','.join(lines)})"
