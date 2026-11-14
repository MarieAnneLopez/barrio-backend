"""Definición territorial de El Tintal y consultas Overpass del ETL (D38).

No existe en OSM un límite de "barrio El Tintal". El proyecto lo define como la
unión de dos UPZ oficiales de la Localidad de Kennedy: la 78 (Tintal Norte,
con Ciudad Tintal y El Tintal III/IV) y la 79 (Calandaima, con la Biblioteca y
el Parque Metropolitano El Tintal). Cambiar la definición = cambiar esta lista.
"""

UPZ_RELATIONS: dict[int, str] = {
    11360088: "UPZ 78 Tintal Norte",
    11350645: "UPZ 79 Calandaima",
}

# Validación del polígono (PLAN_MAESTRO H7): el centroide debe caer aquí.
CENTROID_LAT = (4.62, 4.66)
CENTROID_LON = (-74.17, -74.13)

# Capas base del mapa local (D5), recortadas al polígono (D4).
LAYERS: dict[str, list[str]] = {
    "vias": ['way["highway"]'],
    "parques": [
        'way["leisure"~"^(park|pitch|playground|garden)$"]',
        'way["landuse"~"^(grass|recreation_ground|village_green)$"]',
        'relation["leisure"="park"]',
    ],
    "edificios": ['way["building"]'],
    "manzanas": ['way["landuse"="residential"]'],
}

# Etiqueta OSM que describe el tipo de cada elemento según la capa.
KIND_KEYS: dict[str, tuple[str, ...]] = {
    "vias": ("highway",),
    "parques": ("leisure", "landuse"),
    "edificios": ("building",),
    "manzanas": ("landuse",),
}

OSM_LICENSE = "© OpenStreetMap contributors, ODbL 1.0"


def _ids() -> str:
    return ",".join(str(i) for i in UPZ_RELATIONS)


def polygon_query() -> str:
    return f"[out:json][timeout:120];relation(id:{_ids()});out geom;"


def layer_query(selectors: list[str]) -> str:
    body = "".join(f"{selector}(area.t);" for selector in selectors)
    return f"[out:json][timeout:180];relation(id:{_ids()});map_to_area->.t;({body});out geom;"


def osm_url(element_type: str, element_id: int) -> str:
    return f"https://www.openstreetmap.org/{element_type}/{element_id}"
