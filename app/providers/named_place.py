"""Respuesta sobre una ficha pública identificada por nombre."""

from collections.abc import Callable
from dataclasses import dataclass

from app.providers.lexicon import has, normalize
from app.providers.model_provider import ChatAction, ChatQuery, Fact, ModelAnswer
from app.providers.official_chat import DETAILS, HOURS


@dataclass(frozen=True)
class NamedPlace:
    nombre: str
    slug: str
    item_id: int
    direccion: str | None
    descripcion: str | None


PlaceLookup = Callable[[ChatQuery], NamedPlace | None]


def answer_about_place(place: NamedPlace, query: ChatQuery) -> ModelAnswer:
    text = normalize(query.texto)
    lang = 0 if query.idioma == "es" else 1
    about_address = has(text, ("direcci", "address", "donde", "where", "llegar", "get there"))
    generic = (f"Encontré la ficha de {place.nombre} en El Tintal.",
               f"I found the listing for {place.nombre} in El Tintal.")[lang]
    if has(text, HOURS + ("telefon", "phone", "programacion", "event", "abren")):
        message = (f"No tengo ese dato actualizado de {place.nombre}. Revisa la fuente en su ficha antes de ir.",
                   f"I can't confirm that detail for {place.nombre}. Check the source in its listing before you go.")[lang]
    elif about_address:
        if place.direccion:
            message = (f"La ficha de {place.nombre} indica esta dirección: {place.direccion}.",
                       f"{place.nombre} is listed at {place.direccion}.")[lang]
        else:
            message = (f"{generic} Abre la ficha para ver su ubicación en el mapa.",
                       f"{generic} Open the listing to locate it on the map.")[lang]
    else:
        message = f"{generic} {place.descripcion}" if place.descripcion else generic
    action = ChatAction(f"/categorias/{place.slug}?lugar={place.item_id}", ("Ficha", "Listing")[lang])
    return ModelAnswer("lugar", message, "wave", "analitico", acciones=(action,), lugar=place.nombre,
                       datos=(Fact(place.nombre, place.slug, place.item_id),))


def is_followup(query: ChatQuery) -> bool:
    return query.contexto_lugar is not None and has(normalize(query.texto), DETAILS)
