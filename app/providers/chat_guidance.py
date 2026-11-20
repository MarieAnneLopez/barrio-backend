"""Respuestas deterministas cuando la prioridad es orientar sin otra consulta."""

from app.providers.intents import classify
from app.providers.lexicon import category_from_path, category_name, has, normalize
from app.providers.model_provider import ChatAction, ChatQuery, ModelAnswer
from app.providers.site_context import DEFINITION

URGENT = (
    "me estan robando", "me acaban de robar", "me estan siguiendo", "me estan atacando",
    "hay un herido", "hay una herida", "sangra mucho", "no puede respirar", "no puedo respirar",
    "hay un incendio", "estan disparando", "emergencia ahora", "necesito una ambulancia",
    "being robbed", "just got robbed", "being followed", "being attacked", "someone is injured",
    "can.t breathe", "there.s a fire", "shooting right now", "need an ambulance", "emergency right now",
)
UNSAFE = (
    r"como (?:puedo )?(?:robar|asaltar|atacar|matar|disparar|evadir|esquivar)\b",
    r"how (?:do i |can i |to )(?:rob|attack|kill|shoot|evade|bypass)\b",
    r"(?:evitar|esquivar|evadir|avoid|evade|bypass) (?:a la |las |los |the )?(?:camaras|cameras|policia|police)",
)


def safety_answer(query: ChatQuery) -> ModelAnswer | None:
    text = normalize(query.texto)
    spanish = query.idioma == "es"
    if has(text, URGENT):
        reply = ("Si esto está pasando ahora o alguien está en peligro, llama al 123 en Bogotá."
                 if spanish else "If this is happening now or someone is in danger, call 123 in Bogotá.")
        return ModelAnswer("emergencia", reply, "alert", "analitico")
    if has(text, UNSAFE):
        reply = ("Puedo orientarte sobre prevención y atención oficial en El Tintal."
                 if spanish else "I can help with prevention and official support in El Tintal.")
        return ModelAnswer("prevencion", reply, "alert", "analitico", acciones=(
            ChatAction("/categorias/atencion-inmediata", category_name("atencion-inmediata", query.idioma)),
        ))
    return None


def static_reply(query: ChatQuery, model: str = "analitico:respaldo") -> ModelAnswer:
    intent = classify(query)
    spanish = query.idioma == "es"
    lang = 0 if spanish else 1
    if slug := intent.slug or category_from_path(query.ruta):
        name = category_name(slug, query.idioma)
        message = (f"Abre {name} para consultar las fichas y sus fuentes. Si buscas un lugar, dime su nombre.",
                   f"Open {name} to explore listings and sources. If you need a place, tell me its name.")[lang]
        action = ChatAction(f"/categorias/{slug}", name)
    elif intent.name == "historia":
        message = ("En Historia Local puedes ver la cronología y las fuentes de El Tintal y Kennedy.",
                   "Explore the El Tintal and Kennedy timeline and its sources in Local History.")[lang]
        action = ChatAction("/historia", ("Historia Local", "Local History")[lang])
    elif has(normalize(query.texto), ("el tintal", "tintal norte", "calandaima")):
        message = DEFINITION[query.idioma]
        action = ChatAction("/mapa", ("Mapa de El Tintal", "El Tintal map")[lang])
    else:
        message = ("Puedo orientarte sobre El Tintal. Dime qué lugar o servicio buscas y abre el mapa para explorar.",
                   "I can guide you around El Tintal. Tell me the place or service you need, and explore the map.")[lang]
        action = ChatAction("/mapa", ("Mapa de El Tintal", "El Tintal map")[lang])
    return ModelAnswer(intent.name, message, "idle", model, acciones=(action,))
