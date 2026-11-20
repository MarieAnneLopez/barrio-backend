"""Busca nombres de lugares verificables en las fichas públicas del barrio."""

import re
from typing import Any

from sqlalchemy import String, func, literal, select, union_all
from sqlalchemy.orm import Session

from app.models.mixins import published
from app.modules.registry import MODULES
from app.modules.spec import ModuleSpec
from app.providers.intents import classify
from app.providers.lexicon import category_in, normalize
from app.providers.model_provider import ChatQuery
from app.providers.named_place import NamedPlace, is_followup
from app.providers.official_chat import DETAILS
from app.providers.lexicon import has

EXCLUDED = {"datos-catastrales", "estado-calles", "robos", "localidad", "camaras-seguridad"}


def _clean(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", normalize(text)))


def _candidates(spec: ModuleSpec, text: str, context: str, language: str) -> Any:
    model: Any = spec.model
    name = getattr(model, spec.label_field)
    folded = func.translate(func.lower(name), "áéíóúüñ", "aeiouun")
    cleaned = func.btrim(func.regexp_replace(folded, "[^a-z0-9]+", " ", "g"))
    direct = func.strpos(literal(f" {text} "), func.concat(" ", cleaned, " ")) > 0
    direct = direct & (func.length(cleaned) >= 5)
    matching_context = cleaned == context if context else literal(False)
    address = getattr(model, "direccion", literal(None, String))
    description = getattr(model, f"descripcion_{language}")
    return (select(name.label("nombre"), literal(spec.slug).label("slug"), model.id.label("item_id"),
                   address.label("direccion"), description.label("descripcion"), direct.label("asked"))
            .where(published(model), model.verified.is_(True), name.is_not(None),
                   (model.source_ref.is_distinct_from("dato de ejemplo")), direct | matching_context))


class SqlNamedPlaces:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find(self, query: ChatQuery) -> NamedPlace | None:
        normalized = normalize(query.texto)
        if classify(query).name not in ("desconocido", "categoria") and not has(normalized, DETAILS):
            return None
        text = _clean(query.texto)
        category = category_in(normalized)
        context = _clean(query.contexto_lugar or "") if is_followup(query) else ""
        specs = [spec for spec in MODULES if spec.slug not in EXCLUDED and (category is None or spec.slug == category)]
        if not specs:
            return None
        matches = union_all(*[_candidates(spec, text, context, query.idioma) for spec in specs]).subquery()
        stmt = select(matches).order_by(matches.c.asked.desc(), func.length(matches.c.nombre).desc()).limit(2)
        rows = self._session.execute(stmt).all()
        if not rows:
            return None
        first = rows[0]
        if len(rows) > 1 and first.asked == rows[1].asked and first.nombre == rows[1].nombre:
            return None
        return NamedPlace(first.nombre, first.slug, first.item_id, first.direccion, first.descripcion)
