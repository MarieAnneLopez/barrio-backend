"""Vocabulario del chat: nombres de los 14 módulos (ES/EN) y raíces que los reconocen.

Mismas raíces que el chat local del frontend (chatLocalReplies.ts, H13), para
que la conversación no cambie de comportamiento al pasar al backend.
"""

import re
import unicodedata

from app.providers.model_provider import Language

# slug: (nombre ES, nombre EN, raíces sin tildes; casan al inicio de una palabra)
CATEGORIES: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "centros-educativos": ("Centros Educativos", "Schools",
                           ("colegio", "escuela", "jardin", "universidad", "educa", "school")),
    "escenarios-deportivos": ("Escenarios Deportivos", "Sports Venues",
                              ("cancha", "deporte", "deportivo", "sport", "futbol")),
    "camaras-seguridad": ("Cámaras de Seguridad", "Security Cameras", ("camara", "camera", "vigilancia")),
    "zonas-verdes": ("Zonas Verdes", "Green Areas", ("parque", "zona verde", "park", "arbol", "green")),
    "datos-catastrales": ("Datos Catastrales", "Cadastral Data",
                          ("catastr", "predio", "estrato", "avaluo", "cadastr", "lote")),
    "estado-calles": ("Estado de Calles", "Street Conditions",
                      ("calle", r"vias?(?![a-z])", "street", "road", "hueco")),
    "estaciones-transporte": ("Estaciones de Transporte", "Transit Stations",
                              ("transmilenio", "estacion", r"bus(es)?(?![a-z])", "transporte", "transport",
                               "station")),
    "sitios-comida": ("Sitios de Comida", "Places to Eat",
                      ("comida", "restaurante", "comer", "food", "restaurant", r"eat(?![a-z])")),
    "librerias": ("Librerías", "Bookstores", ("libreria", "libro", "book", "papeleria")),
    "robos": ("Datos sobre Robos", "Theft Data", ("robo", "hurto", "inseguridad", "theft", "robbery", "crime")),
    "localidad": ("Información de la Localidad", "Locality Information",
                  ("kennedy", "localidad", "district", "alcaldia")),
    "atencion-inmediata": ("Atención Inmediata", "Emergency Services",
                           ("hospital", r"cami(?![a-z])", "urgencia", "salud", "clinic", "health", "emergenc")),
    "veterinarias": ("Veterinarias", "Veterinary Clinics",
                     ("veterinari", "mascota", "perro", "gato", r"vets?(?![a-z])", r"pets?(?![a-z])")),
    "barberias": ("Barberías", "Barbershops", ("barber", "peluquer", "corte", "haircut")),
}


def normalize(text: str) -> str:
    """Minúsculas y sin tildes, para comparar sin depender de cómo se escriba."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def has(text: str, words: tuple[str, ...]) -> bool:
    return re.search(rf"(^|[^a-z])(?:{'|'.join(words)})", text) is not None


def category_in(text: str) -> str | None:
    """Primer módulo nombrado en un texto ya normalizado."""
    return next((slug for slug, (_, _, words) in CATEGORIES.items() if has(text, words)), None)


def category_name(slug: str, lang: Language) -> str:
    es, en, _ = CATEGORIES[slug]
    return es if lang == "es" else en


def category_from_path(path: str | None) -> str | None:
    """El agente percibe la página: /categorias/<slug> le dice de qué módulo se habla."""
    match = re.fullmatch(r"/categorias/([a-z-]+)/?", path or "")
    return match.group(1) if match and match.group(1) in CATEGORIES else None
