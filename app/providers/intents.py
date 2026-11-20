"""Clasificación de intención y extracción de entidades (parte analítica del modelo).

Reglas deterministas sobre el texto normalizado: no necesitan internet ni
claves, y cada intención tiene su prueba. El orden importa: «¿cuántos colegios
hay?» es una estadística, no una lista, y «el mejor restaurante» es ranking.
"""

from dataclasses import dataclass

from app.providers.lexicon import category_from_path, category_in, has, normalize
from app.providers.model_provider import ChatQuery

# «Marie» sola no basta: el asistente se llama Mini Marie y aparece en los saludos.
CONTACT = ("whatsapp", "contact", "creadora", "creator", "telefono", "phone", "quien creo", "who made")
CREATOR = ("creadora", "creator", "quien creo", "who made")
STATS = ("cuant", "estadistic", "how many", "stats", "total", "numero de", "number of")
BEST = ("mejor", "top", "best", "recomiend", "recommend", "calificad", "rated", "favorit")
NEAR = ("cerca", "near", "proxim", "closest", "nearest")
HISTORY = ("historia", "history", "hacienda", "origen", "fundad", "techo", "bandera", "flag")
MAP = ("mapa", "map", "3d", "maqueta")
HELP = ("ayuda", "help", "puedes", "can you", "como funciona", "how does", "que sabes")
GREET = (r"hola(?![a-z])", "buenas", r"hello(?![a-z])", r"hi(?![a-z])", r"hey(?![a-z])", "saludos",
         "buenos dias", "good morning")

# Dominio de cada intención para el enrutador MoE.
DOMAINS = {
    "categoria": "espacial", "robos": "espacial", "cercania": "espacial", "mejor_calificado": "espacial",
    "estadisticas": "espacial", "historia": "documental", "localidad": "documental",
    "saludo": "conversacional", "ayuda": "conversacional", "contacto": "conversacional",
    "mapa": "conversacional", "desconocido": "conversacional",
}


@dataclass(frozen=True)
class Intent:
    name: str
    slug: str | None = None


def classify(query: ChatQuery) -> Intent:
    text = normalize(query.texto)
    slug = category_in(text)
    if has(text, CONTACT) and (slug is None or has(text, CREATOR)):
        return Intent("contacto")
    if has(text, STATS):
        return Intent("estadisticas", slug)
    if has(text, BEST):
        return Intent("mejor_calificado", slug or category_from_path(query.ruta))
    if has(text, NEAR):
        return Intent("cercania", slug or category_from_path(query.ruta))
    if has(text, HISTORY) or slug == "localidad":
        return Intent("localidad" if slug == "localidad" and not has(text, HISTORY) else "historia")
    if slug is not None:
        return Intent("robos" if slug == "robos" else "categoria", slug)
    for name, words in (("mapa", MAP), ("ayuda", HELP), ("saludo", GREET)):
        if has(text, words):
            return Intent(name)
    return Intent("desconocido")
