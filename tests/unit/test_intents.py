"""Clasificación de intención y extracción del módulo (H22): un caso o más por intención, ES y EN."""

import pytest

from app.providers.intents import DOMAINS, classify
from app.providers.lexicon import category_from_path, normalize
from app.providers.model_provider import ChatQuery


@pytest.mark.parametrize("texto, intent, slug", [
    ("¡Hola, Mini Marie!", "saludo", None),
    ("Hi there", "saludo", None),
    ("¿Qué puedes hacer? Ayuda", "ayuda", None),
    ("¿Cómo contacto a Marie?", "contacto", None),
    ("Give me the creator's WhatsApp", "contacto", None),
    ("¿Qué colegios hay en El Tintal?", "categoria", "centros-educativos"),
    ("Muéstrame sitios de comida", "categoria", "sitios-comida"),
    ("What schools are there?", "categoria", "centros-educativos"),
    ("¿Cuál es la veterinaria mejor calificada?", "mejor_calificado", "veterinarias"),
    ("best rated barbershop", "mejor_calificado", "barberias"),
    ("¿Qué queda más cerca?", "cercania", None),
    ("parques cerca de mí", "cercania", "zonas-verdes"),
    ("¿Cuántos lugares hay registrados?", "estadisticas", None),
    ("how many vets are there", "estadisticas", "veterinarias"),
    ("Cuéntame la historia del barrio", "historia", None),
    ("historia de Kennedy", "historia", None),
    ("información de la localidad", "localidad", None),
    ("¿Hay robos en el barrio?", "robos", "robos"),
    ("¿Qué hay en el mapa 3D?", "mapa", None),
    ("qwerty asdf", "desconocido", None),
])
def test_cada_intencion(texto: str, intent: str, slug: str | None) -> None:
    result = classify(ChatQuery(texto))
    assert (result.name, result.slug) == (intent, slug)
    assert result.name in DOMAINS


def test_la_pagina_actual_completa_el_modulo() -> None:
    query = ChatQuery("¿Cuál es el mejor?", ruta="/categorias/barberias")
    assert classify(query).slug == "barberias"
    assert classify(ChatQuery("¿Qué queda cerca?", ruta="/categorias/no-existe")).slug is None


def test_normaliza_y_lee_la_ruta() -> None:
    assert normalize("CÁMARAS Ñandú") == "camaras nandu"
    assert category_from_path("/categorias/zonas-verdes") == "zonas-verdes"
    assert category_from_path("/historia") is None and category_from_path(None) is None
