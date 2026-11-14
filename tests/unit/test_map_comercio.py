"""Mapeos OSM de comercio, áreas y calles: solo lo que OSM dice, nada inventado."""

from etl.modules import areas, calles, comercio
from etl.modules.common import center, phone


def _el(**tags: str) -> dict:
    return {"type": "node", "id": 9, "tags": tags, "lat": 4.65, "lon": -74.15}


def test_comida_usa_la_cocina_o_el_tipo_de_local() -> None:
    props, _ = comercio.map_food(_el(name="Donde María", amenity="restaurant", cuisine="regional"))
    fast, _ = comercio.map_food(_el(name="Mc", amenity="fast_food"))

    assert props is not None and props["especialidad"] == "comida típica"
    assert fast is not None and fast["especialidad"] == "Comida rápida"
    assert props["source_ref"] == "https://www.openstreetmap.org/node/9" and props["verified"]


def test_sin_nombre_se_omite_en_todos_los_comercios() -> None:
    for mapper in (comercio.map_food, comercio.map_book, comercio.map_vet, comercio.map_barber):
        assert mapper(_el(amenity="cafe")) == (None, "sin nombre")


def test_libreria_y_veterinaria_no_inventan_servicios() -> None:
    book, _ = comercio.map_book(_el(name="Papelería Sol", shop="stationery", opening_hours="Mo-Sa 08:00-18:00"))
    vet, _ = comercio.map_vet(_el(name="Vet Tintal", amenity="veterinary"))

    assert book is not None and book["especialidad"] == "Papelería" and book["horario"] == "Mo-Sa 08:00-18:00"
    assert vet is not None and vet["servicios"] is None


def test_peluqueria_sin_evidencia_no_es_barberia() -> None:
    assert comercio.map_barber(_el(name="Sala de Belleza", shop="hairdresser"))[1] == \
        "peluquería sin evidencia de barbería"
    assert comercio.map_barber(_el(name="Barbería Kings", shop="hairdresser"))[0] is not None
    assert comercio.map_barber(_el(name="Estilo", shop="hairdresser", hairdresser="barber"))[0] is not None


def test_telefono_invalido_se_descarta_y_se_toma_el_primero() -> None:
    assert phone({"phone": "+57 601 4481400;+57 300"}) == "+57 601 4481400"
    assert phone({"phone": "llamar al portero"}) is None
    assert center(_el()) == {"type": "Point", "coordinates": [-74.15, 4.65]}


def test_escenario_sin_nombre_recibe_nombre_descriptivo_por_verificar() -> None:
    props, _ = areas.map_sport(_el(leisure="pitch", sport="soccer;basketball", lit="yes", fee="yes"))

    assert props is not None
    assert props["nombre"] == "Cancha de fútbol, baloncesto" and props["verified"] is False
    assert props["iluminacion"] is True and props["acceso"] == "pago"


def test_escenario_sin_nombre_ni_deporte_se_omite() -> None:
    assert areas.map_sport(_el(leisure="pitch")) == (None, "sin nombre ni deporte")


def test_escenario_con_nombre_sin_deporte_queda_por_verificar() -> None:
    props, _ = areas.map_sport(_el(leisure="sports_centre", name="Polideportivo", access="private"))

    assert props is not None and props["deportes"] == "por verificar" and props["acceso"] == "restringido"


def test_zonas_verdes_tipo_por_etiqueta_o_nombre() -> None:
    alameda, _ = areas.map_green(_el(leisure="park", name="Alameda El Porvenir"))
    jardin, _ = areas.map_green(_el(leisure="garden"))

    assert alameda is not None and alameda["tipo"] == "alameda" and alameda["verified"] is True
    assert jardin is not None and jardin["tipo"] == "jardin" and jardin["verified"] is False


def test_calle_solo_es_mala_por_la_regla_del_idu() -> None:
    tierra, _ = calles.map_element(_el(highway="residential", name="Calle 6", surface="dirt"))
    asfalto, _ = calles.map_element(_el(highway="primary_link", name="Av. Cali", surface="asphalt"))

    assert tierra is not None and tierra["estado"] == "malo" and tierra["material"] == "tierra"
    assert asfalto is not None and asfalto["estado"] is None and asfalto["tipo_via"] == "arterial principal"
