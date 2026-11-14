"""Textos del modelo analítico en español e inglés, con números y listas según el idioma."""

from app.providers.model_provider import Language

PHRASES: dict[str, dict[str, str]] = {
    "es": {
        "saludo": "¡Hola! Soy Mini Marie. Pregúntame por los 14 módulos del barrio, lo mejor calificado, "
                  "lo que queda cerca o la historia de El Tintal.",
        "ayuda": "Puedo decirte qué hay en cada módulo (colegios, parques, comida, transporte…), cuál es el "
                 "lugar mejor calificado, qué queda cerca, cuántos registros hay y la historia del barrio.",
        "contacto": "Marie Anne Lopez Poveda creó esta plataforma. Puedes escribirle por WhatsApp al "
                    "313 259 6937 o ver su perfil.",
        "categoria": "En {name} hay {total} registros ({verified} verificados). Por ejemplo: {examples}.",
        "categoria_vacia": "En {name} todavía no hay registros cargados.",
        "robos_aviso": " Son reportes para prevenir, no para alarmarte. En una emergencia llama al 123.",
        "mejor": "Lo mejor calificado{scope} es {nombre}: {promedio} de 5 estrellas con {votos} calificaciones.",
        "mejor_vacio": "Todavía no hay calificaciones{scope}. Puedes ser la primera persona en calificar.",
        "cerca": "Cerca {where} están: {places}.",
        "cerca_vacio": "No encontré lugares{scope} a menos de 1,5 km {where}.",
        "aqui": "de tu ubicación", "centro": "del centro de El Tintal", "en": " en {name}",
        "stats_modulo": "En {name} hay {total} registros, {verified} de ellos verificados.",
        "stats": "La plataforma tiene {total} registros en 14 módulos y {ratings} calificaciones. "
                 "Los módulos con más datos son {top}.",
        "historia": "Algunos hitos: {items}. En Historia Local cada uno tiene su fuente.",
        "historia_vacia": "La historia del barrio todavía no está cargada.",
        "localidad": "El Tintal queda en la Localidad de {nombre}: {poblacion} habitantes y {area} km².",
        "mapa": "El mapa 3D muestra las manzanas, vías y parques de El Tintal con los lugares de cada módulo.",
        "desconocido": "No entendí bien. Puedo contarte de los 14 módulos, lo mejor calificado, lo que queda "
                       "cerca, estadísticas o la historia del barrio.",
        "y": "y", "metros": "{m} m",
        "q_colegios": "¿Qué colegios hay en El Tintal?", "q_mejor": "¿Cuál es la veterinaria mejor calificada?",
        "q_cerca": "¿Qué queda más cerca?", "q_historia": "Cuéntame la historia del barrio",
        "q_stats": "¿Cuántos lugares hay registrados?",
    },
    "en": {
        "saludo": "Hi! I'm Mini Marie. Ask me about the neighborhood's 14 modules, the best-rated places, "
                  "what's nearby or the history of El Tintal.",
        "ayuda": "I can tell you what each module has (schools, parks, food, transit…), the best-rated place, "
                 "what's nearby, how many records there are and the neighborhood's history.",
        "contacto": "Marie Anne Lopez Poveda created this platform. You can message her on WhatsApp at "
                    "+57 313 259 6937 or see her profile.",
        "categoria": "{name} has {total} records ({verified} verified). For example: {examples}.",
        "categoria_vacia": "{name} has no records loaded yet.",
        "robos_aviso": " These reports are for prevention, not alarm. In an emergency call 123.",
        "mejor": "The best-rated place{scope} is {nombre}: {promedio} out of 5 stars from {votos} ratings.",
        "mejor_vacio": "There are no ratings{scope} yet. You can be the first to rate.",
        "cerca": "Near {where}: {places}.",
        "cerca_vacio": "I found no places{scope} within 1.5 km of {where}.",
        "aqui": "your location", "centro": "the center of El Tintal", "en": " in {name}",
        "stats_modulo": "{name} has {total} records, {verified} of them verified.",
        "stats": "The platform has {total} records across 14 modules and {ratings} ratings. "
                 "The modules with the most data are {top}.",
        "historia": "Some milestones: {items}. Each one has its source in Local History.",
        "historia_vacia": "The neighborhood's history isn't loaded yet.",
        "localidad": "El Tintal is in the {nombre} Locality: {poblacion} residents and {area} km².",
        "mapa": "The 3D map shows El Tintal's blocks, streets and parks with the places of every module.",
        "desconocido": "I didn't quite get that. I can tell you about the 14 modules, the best-rated places, "
                       "what's nearby, statistics or the neighborhood's history.",
        "y": "and", "metros": "{m} m",
        "q_colegios": "What schools are in El Tintal?", "q_mejor": "Which vet is the best rated?",
        "q_cerca": "What's nearby?", "q_historia": "Tell me the neighborhood's history",
        "q_stats": "How many places are registered?",
    },
}


def say(lang: Language, key: str, **values: object) -> str:
    return PHRASES[lang][key].format(**values)


def number(value: float, lang: Language, decimals: int = 0) -> str:
    text = f"{value:,.{decimals}f}"
    return text.translate(str.maketrans(",.", ".,")) if lang == "es" else text


def listing(items: list[str], lang: Language) -> str:
    if len(items) <= 1:
        return "".join(items)
    return f"{', '.join(items[:-1])} {PHRASES[lang]['y']} {items[-1]}"
