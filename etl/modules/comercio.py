"""OSM → Módulos de comercio de puntos: 8 Sitios de Comida, 9 Librerías, 13 Veterinarias.

Solo se copian datos que OSM trae; calificación y rango de precios quedan nulos
(los da el ranking de H18, no la fuente).
"""

from typing import Any

from etl.modules.common import Mapped, address, hours, name_of, tags_of, trace, translate

FOOD = {"restaurant": "Restaurante", "fast_food": "Comida rápida", "cafe": "Café",
        "food_court": "Plazoleta de comidas", "ice_cream": "Heladería"}
CUISINE = {"pizza": "pizza", "burger": "hamburguesas", "chicken": "pollo", "coffee_shop": "café",
           "regional": "comida típica", "ice_cream": "helados", "sandwich": "sándwiches",
           "bakery": "panadería", "colombian": "comida colombiana", "seafood": "mariscos"}
BOOKS = {"books": "Libros", "stationery": "Papelería"}


def _base(element: dict[str, Any]) -> tuple[dict[str, str], str]:
    tags = tags_of(element)
    return tags, name_of(tags)


def map_food(element: dict[str, Any]) -> Mapped:
    tags, name = _base(element)
    if not name:
        return None, "sin nombre"
    especialidad = translate(tags.get("cuisine"), CUISINE) or FOOD.get(tags.get("amenity", ""))
    return {"nombre": name, "especialidad": (especialidad or "")[:120] or None,
            "direccion": address(tags), "horario": hours(tags), **trace(element)}, None


def map_book(element: dict[str, Any]) -> Mapped:
    tags, name = _base(element)
    if not name:
        return None, "sin nombre"
    return {"nombre": name, "direccion": address(tags), "horario": hours(tags),
            "especialidad": BOOKS.get(tags.get("shop", "")), **trace(element)}, None


def map_vet(element: dict[str, Any]) -> Mapped:
    tags, name = _base(element)
    if not name:
        return None, "sin nombre"
    return {"nombre": name, "servicios": None, "direccion": address(tags),
            "horario": hours(tags), **trace(element)}, None


def _is_barber(tags: dict[str, str], name: str) -> bool:
    return (tags.get("shop") == "barber" or tags.get("hairdresser") in ("barber", "men")
            or "barber" in name.lower())


def map_barber(element: dict[str, Any]) -> Mapped:
    tags, name = _base(element)
    if not name:
        return None, "sin nombre"
    if not _is_barber(tags, name):
        return None, "peluquería sin evidencia de barbería"
    return {"nombre": name, "direccion": address(tags), "horario": hours(tags),
            "servicios": None, **trace(element)}, None


class Module:
    """Adaptador al contrato de etl/modules/common.py para cada módulo de comercio."""

    GEOMETRY = "point"

    def __init__(self, slug: str, selectors: list[str], mapper: Any) -> None:
        self.SLUG, self.SELECTORS, self.map_element = slug, selectors, mapper


COMIDA = Module("sitios-comida",
                ['nwr["amenity"~"^(restaurant|fast_food|cafe|food_court|ice_cream)$"]'], map_food)
LIBRERIAS = Module("librerias", ['nwr["shop"~"^(books|stationery)$"]'], map_book)
VETERINARIAS = Module("veterinarias", ['nwr["amenity"="veterinary"]'], map_vet)
BARBERIAS = Module("barberias", ['nwr["shop"~"^(barber|hairdresser)$"]'], map_barber)
