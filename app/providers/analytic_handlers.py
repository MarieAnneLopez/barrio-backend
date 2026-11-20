"""Respuestas del modelo analítico que consultan datos reales del barrio (BarrioTools)."""

from app.providers.intents import Intent
from app.providers.lexicon import category_name
from app.providers.model_provider import ChatAction, ChatQuery, Fact, ModelAnswer
from app.providers.phrases import listing, number, say
from app.providers.tools import BarrioTools

NAME = "analitico"


def to_module(slug: str, query: ChatQuery) -> ChatAction:
    return ChatAction(f"/categorias/{slug}", category_name(slug, query.idioma))


def category(intent: Intent, query: ChatQuery, tools: BarrioTools) -> ModelAnswer:
    slug, lang = intent.slug or "", query.idioma
    info = tools.summary(slug)
    name = category_name(slug, lang)
    mark = "dato de ejemplo" if lang == "es" else "sample data"
    examples = [f"{n} ({mark})" if n in info.ficticios else n for n in info.ejemplos]
    text = (say(lang, "categoria", name=name, total=number(info.total, lang), verified=number(info.verified, lang),
                examples=listing(examples, lang))
            if info.total else say(lang, "categoria_vacia", name=name))
    alert = slug == "robos"
    if alert:
        text += say(lang, "robos_aviso")
    facts = tuple(Fact(n, slug, detalle=mark if n in info.ficticios else None) for n in info.ejemplos)
    return ModelAnswer(intent.name, text, "alert" if alert else "wave", NAME, acciones=(to_module(slug, query),),
                       datos=facts)


def best(intent: Intent, query: ChatQuery, tools: BarrioTools) -> ModelAnswer:
    lang = query.idioma
    scope = say(lang, "en", name=category_name(intent.slug, lang)) if intent.slug else ""
    place = tools.best(intent.slug)
    if place is None:
        actions = (to_module(intent.slug, query),) if intent.slug else ()
        return ModelAnswer(intent.name, say(lang, "mejor_vacio", scope=scope), "idle", NAME, acciones=actions)
    decimals = 1 if round(place.promedio, 1) == place.promedio else 2
    text = say(lang, "mejor", scope=scope, nombre=place.nombre, promedio=number(place.promedio, lang, decimals),
               votos=number(place.votos, lang))
    return ModelAnswer(intent.name, text, "jump", NAME, acciones=(to_module(place.slug, query),),
                       datos=(Fact(place.nombre, place.slug, place.objeto_id, f"{place.promedio}/5"),))


def nearby(intent: Intent, query: ChatQuery, tools: BarrioTools) -> ModelAnswer:
    lang = query.idioma
    located = query.lon is not None and query.lat is not None
    lon, lat = (query.lon, query.lat) if located else tools.center()
    where = say(lang, "aqui" if located else "centro")
    scope = say(lang, "en", name=category_name(intent.slug, lang)) if intent.slug else ""
    places = tools.nearest(float(lon or 0), float(lat or 0), intent.slug)
    if not places:
        return ModelAnswer(intent.name, say(lang, "cerca_vacio", scope=scope, where=where), "idle", NAME)
    labels = [f"{p.nombre} ({say(lang, 'metros', m=number(p.distancia_m, lang))})" for p in places]
    actions = tuple(dict.fromkeys(to_module(p.slug, query) for p in places))
    facts = tuple(Fact(p.nombre, p.slug, p.objeto_id, f"{p.distancia_m} m") for p in places)
    return ModelAnswer(intent.name, say(lang, "cerca", where=where, places=listing(labels, lang)), "wave", NAME,
                       acciones=actions, datos=facts)


def stats(intent: Intent, query: ChatQuery, tools: BarrioTools) -> ModelAnswer:
    lang = query.idioma
    if intent.slug:
        info = tools.summary(intent.slug)
        text = say(lang, "stats_modulo", name=category_name(intent.slug, lang), total=number(info.total, lang),
                   verified=number(info.verified, lang))
        return ModelAnswer(intent.name, text, "idle", NAME, acciones=(to_module(intent.slug, query),))
    totals = tools.totals()
    top = sorted(totals, key=lambda s: (-totals[s], s))[:3]
    text = say(lang, "stats", total=number(sum(totals.values()), lang), ratings=number(tools.ratings_count(), lang),
               top=listing([f"{category_name(s, lang)} ({number(totals[s], lang)})" for s in top], lang))
    return ModelAnswer(intent.name, text, "idle", NAME, acciones=(ChatAction("/ranking", "Ranking"),))
