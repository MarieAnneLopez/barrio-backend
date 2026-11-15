"""Respuestas de historia y localidad (experto documental) y de conversación sin datos."""

from app.providers.intents import Intent
from app.providers.model_provider import ChatAction, ChatQuery, Expression, ModelAnswer
from app.providers.phrases import listing, number, say
from app.providers.tools import BarrioTools

NAME = "analitico"
HISTORY_PAGE = {"es": "Historia Local", "en": "Local History"}
CREATOR_PAGE = {"es": "Perfil de la Creadora", "en": "Creator Profile"}
MAP_PAGE = {"es": "Mapa 3D", "en": "3D Map"}


def history(intent: Intent, query: ChatQuery, tools: BarrioTools) -> ModelAnswer:
    lang = query.idioma
    action = (ChatAction("/historia", HISTORY_PAGE[lang]),)
    # Solo hitos confirmados por una fuente oficial; los de prensa se ven en la página con su etiqueta.
    hitos = [h for h in tools.milestones() if h.verified][:4]
    if not hitos:
        return ModelAnswer(intent.name, say(lang, "historia_vacia"), "idle", NAME, acciones=action)
    items = listing([f"{h.anio}: {h.titulo}" for h in hitos], lang)
    return ModelAnswer(intent.name, say(lang, "historia", items=items), "wave", NAME, acciones=action)


def locality(intent: Intent, query: ChatQuery, tools: BarrioTools) -> ModelAnswer:
    lang = query.idioma
    info = tools.locality()
    action = (ChatAction("/categorias/localidad", "Kennedy"),)
    if info is None or info.poblacion is None or info.superficie_km2 is None:
        return history(intent, query, tools)
    text = say(lang, "localidad", nombre=info.nombre, poblacion=number(info.poblacion, lang),
               area=number(info.superficie_km2, lang, 2))
    return ModelAnswer(intent.name, text, "wave", NAME, acciones=action)


def conversation(intent: Intent, query: ChatQuery, tools: BarrioTools) -> ModelAnswer:
    """Saludo, ayuda, contacto, mapa y lo no entendido: texto fijo con sugerencias."""
    lang = query.idioma
    actions = {
        "contacto": (ChatAction("/creadora", CREATOR_PAGE[lang]),),
        "mapa": (ChatAction("/mapa", MAP_PAGE[lang]),),
    }.get(intent.name, ())
    expressions: dict[str, Expression] = {"saludo": "wave", "desconocido": "sad"}
    expression: Expression = expressions.get(intent.name, "idle")
    suggestions = tuple(say(lang, k) for k in ("q_colegios", "q_mejor", "q_cerca", "q_historia", "q_stats"))
    return ModelAnswer(intent.name, say(lang, intent.name), expression,
                       NAME, acciones=actions, sugerencias=suggestions if intent.name != "contacto" else ())
