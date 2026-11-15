"""Contexto público del chat con IA (H36): solo lo que la plataforma ya muestra.

Sale de la base (totales, nombres de lugares, historia, localidad) y de los textos
de la página copiados tal cual: la definición del barrio (frontend, es/en.json
«locator.definition») y los nombres del menú («nav»). Fuera quedan los datos
personales de la creadora: no se envían a un proveedor externo.
"""

import time
from collections import Counter

from app.providers.lexicon import CATEGORIES
from app.providers.model_provider import Language
from app.providers.tools import BarrioTools

DEFINITION = {
    "es": "En esta plataforma, El Tintal es la suma de las UPZ 78 Tintal Norte (343 ha) y 79 Calandaima (319 ha): "
          "662 ha según la SDP (2012), vía Catastro Bogotá. Es una definición operativa, no una unidad "
          "administrativa oficial. El Portal Américas queda fuera, a unos 1,3 km al sur (UPZ 83 Las Margaritas).",
    "en": "On this platform, El Tintal is UPZ 78 Tintal Norte (343 ha) plus UPZ 79 Calandaima (319 ha): 662 ha "
          "according to the SDP (2012), via Catastro Bogotá. It is an operational definition, not an official "
          "administrative unit. Portal Américas lies outside, about 1.3 km to the south (UPZ 83 Las Margaritas).",
}
SECTIONS = {
    "es": "Secciones del menú: Inicio (maqueta 3D), Mapa 3D (mapas temáticos), Historia Local (línea de tiempo, "
          "bandera de Kennedy y mapa de ubicación con la definición del barrio), Ranking de Calificaciones "
          "(lugares mejor calificados), Galería General (fotos libres de Wikimedia Commons), Preguntas Frecuentes, "
          "Perfil de la Creadora, Ayuda y Categorías (los 14 módulos). Cada módulo tiene mapa, lista con búsqueda, "
          "ficha de cada lugar con fotos, calificaciones y la fuente del dato. Para calificar un lugar se inicia "
          "sesión y, en su ficha, se eligen de 0,5 a 5 estrellas.",
    "en": "Menu sections: Home (3D model), 3D Map (thematic maps), Local History (timeline, Kennedy flag and "
          "location map with the neighborhood definition), Ratings Ranking (best-rated places), Photo Gallery "
          "(free photos from Wikimedia Commons), FAQ, About the Creator, Help and Categories (the 14 modules). "
          "Each module has a map, a searchable list, a page per place with photos, ratings and the source. To "
          "rate a place, sign in and choose 0.5 to 5 stars on its page.",
}
# Capas de datos: solo totales (miles de lotes y tramos no caben ni ayudan como lista).
DATA_LAYERS = {"datos-catastrales", "estado-calles", "robos", "localidad"}
TTL_S = 300.0
_cache: dict[Language, tuple[float, str]] = {}


STATUS = {
    "es": {"verificado": "verificado", "por_verificar": "por verificar", "ejemplo": "dato de ejemplo"},
    "en": {"verificado": "verified", "por_verificar": "to be verified", "ejemplo": "sample data"},
}


def _places(rows: list[tuple[str, str]], idioma: Language) -> str:
    """Resumen por estado y nombres con su marca (los verificados van sin marca)."""
    labels = STATUS[idioma]
    by_status = Counter(status for _, status in rows)
    head = ", ".join(f"{by_status[k]} {labels[k]}" for k in labels if by_status[k])
    names = Counter(rows)
    listed = "; ".join(f"{n}{'' if st == 'verificado' else f' ({labels[st]})'}{'' if c == 1 else f' ×{c}'}"
                       for (n, st), c in names.items())
    return f"{len(rows)} ({head}): {listed}"


def _build(tools: BarrioTools, idioma: Language) -> str:
    es = idioma == "es"
    lines = ["El Tintal, Kennedy, Bogotá D.C.", DEFINITION[idioma], SECTIONS[idioma], ""]
    lines.append("Módulos y sus registros:" if es else "Modules and their records:")
    verified = STATUS[idioma]["verificado"]
    for slug, (name_es, name_en, _) in CATEGORIES.items():
        name = f"- {name_es if es else name_en} [{slug}]"
        if slug in DATA_LAYERS:
            summary = tools.summary(slug)
            lines.append(f"{name}: {summary.total} ({summary.verified} {verified})")
        else:
            lines.append(f"{name}: {_places(tools.place_names(slug), idioma)}")
    lines.append("")
    lines.append("Historia Local (año: hito):" if es else "Local History (year: milestone):")
    pending = " (por verificar)" if es else " (to be verified)"
    lines += [f"- {m.anio}: {m.titulo}{'' if m.verified else pending}" for m in tools.milestones()]
    locality = tools.locality()
    if locality is not None:
        label, people = ("Localidad", "población") if es else ("Locality", "population")
        lines.append(f"{label}: {locality.nombre}; {people} {locality.poblacion}; {locality.superficie_km2} km²")
    return "\n".join(lines)


def site_context(tools: BarrioTools, idioma: Language, now: float | None = None) -> str:
    """Texto del contexto público, cacheado 5 min por idioma (cada mensaje no recorre la base)."""
    current = time.monotonic() if now is None else now
    cached = _cache.get(idioma)
    if cached is not None and current - cached[0] < TTL_S:
        return cached[1]
    text = _build(tools, idioma)
    _cache[idioma] = (current, text)
    return text


def clear_cache() -> None:
    _cache.clear()
