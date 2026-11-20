"""Orientación sobre la biblioteca y los recorridos publicados por TransMilenio."""

from datetime import UTC, date, datetime
import re

from app.providers.lexicon import has, normalize
from app.providers.model_provider import ChatAction, ChatQuery, ModelAnswer, Source
from app.providers.official_reader import LIBRARY_URL, TRANSIT_URL, LibraryField, read_page

LIBRARY = "Biblioteca Pública El Tintal Manuel Zapata Olivella"
STATION = "Estación Biblioteca El Tintal"
PORTAL = "Portal Américas"
LIBRARY_ALIASES = ("biblioteca", "library", "manuel zapata olivella", "biblored")
STATION_ALIASES = ("estacion biblioteca", "biblioteca el tintal station", "tintal library station")
TRANSIT = ("transmilenio", "transmiapp", "sitp", r"bus(?:es)?\b", "paradero", "station", "estacion")
HOURS = ("horario", "abiert", "abre", "cierr", "hours", "open", "clos", "festivo", "holiday", "hoy", "today")
DETAILS = HOURS + ("programacion", "actividad", "events", "servicio", "services", "telefon", "phone",
                   "direcci", "address", "donde", "where", "llegar", "get there", "ruta", "route", "about")
CHECKED = date(2026, 11, 20)
ENGLISH = {
    "lunes": "Mondays", "martes": "Tuesday", "sábado": "Saturday", "domingos": "Sundays",
    "días festivos": "public holidays", "sin atención": "closed", " a ": " to ", " de ": " from ", " y ": " and ",
}


def _answer(query: ChatQuery, es: str, en: str, name: str | None, source: Source,
            route: str) -> ModelAnswer:
    spanish = query.idioma == "es"
    action = ChatAction(route, "Ver en el sitio" if spanish else "Explore on the site")
    return ModelAnswer("lugar", es if spanish else en, "wave", "analitico", acciones=(action,),
                       fuentes=(source,), lugar=name)


def _library_hours(html: str | None, english: bool) -> str:
    values = LibraryField("node-field-field-horario-string-long").values(html or "")
    if not values or len(values) > 7 or sum(map(len, values)) > 360:
        return ""
    if any(not re.search(r"\d:\d{2}|sin atención|cerrad", line, re.IGNORECASE) for line in values):
        return ""
    text = "\n".join(values)
    if english:
        for original, translated in ENGLISH.items():
            text = re.sub(re.escape(original), translated, text, flags=re.IGNORECASE)
    return text


def _library(query: ChatQuery, text: str) -> ModelAnswer:
    checked = CHECKED
    es = f"La {LIBRARY} queda en la avenida Ciudad de Cali # 6C-09, en Kennedy."
    en = f"{LIBRARY} is at Avenida Ciudad de Cali # 6C-09 in Kennedy."
    if has(text, HOURS):
        hours = _library_hours(read_page(LIBRARY_URL), query.idioma == "en")
        if hours:
            checked = datetime.now(UTC).date()
            es = f"Horario publicado por BibloRed, sujeto a cambios:\n{hours}"
            en = f"BibloRed’s published hours, subject to change:\n{hours}"
        else:
            es, en = ("Consulta el horario actualizado en la ficha oficial de BibloRed.",
                      "Check the BibloRed page for the current opening hours.")
    elif has(text, ("telefon", "phone", "contact")):
        es = "BibloRed indica el (601) 5803060, extensión 1000, para la Biblioteca El Tintal."
        en = "BibloRed lists (601) 5803060, extension 1000, for El Tintal Library."
    elif has(text, ("activid", "events", "servicio", "services", "programacion")):
        es = "Consulta los servicios y la agenda en la ficha oficial de la biblioteca."
        en = "See the library’s official page for services and events."
    return _answer(query, es, en, LIBRARY, Source("BibloRed", LIBRARY_URL, checked), "/historia")


def official_answer(query: ChatQuery) -> ModelAnswer | None:
    text = normalize(query.texto)
    if has(text, ("portal america", "americas portal")):
        name = PORTAL
    elif has(text, STATION_ALIASES) or (has(text, TRANSIT) and has(text, LIBRARY_ALIASES)):
        name = STATION
    elif has(text, LIBRARY_ALIASES):
        return _library(query, text)
    elif has(text, TRANSIT) and has(text, DETAILS):
        name = None
    elif query.contexto_lugar in (PORTAL, STATION) and has(text, DETAILS):
        name = query.contexto_lugar
    elif query.contexto_lugar == LIBRARY and has(text, DETAILS):
        return _library(query, text)
    else:
        return None
    head_es = "El Portal Américas queda fuera del área de El Tintal que cubre la plataforma. " if name == PORTAL else ""
    head_en = "Portal Américas is outside the El Tintal area covered by the site. " if name == PORTAL else ""
    es = head_es + "Consulta en TransMiApp los recorridos, horarios y novedades de TransMilenio y SITP."
    en = head_en + "Check TransMiApp for TransMilenio and SITP routes, schedules and service alerts."
    return _answer(query, es, en, name, Source("TransMilenio · TransMiApp", TRANSIT_URL, CHECKED),
                   "/categorias/estaciones-transporte")
