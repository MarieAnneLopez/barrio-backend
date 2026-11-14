"""AnalyticModel (H22): cada intención responde con datos de las herramientas, en ES y EN."""

from app.providers.analytic_model import AnalyticModel
from app.providers.model_provider import ChatQuery
from tests.unit.chat_fakes import FakeTools


def ask(texto: str, idioma: str = "es", empty: bool = False, **ctx: object):  # type: ignore[no-untyped-def]
    tools = FakeTools(empty=empty)
    return AnalyticModel(tools).answer(ChatQuery(texto, idioma, **ctx)), tools  # type: ignore[arg-type]


def test_categoria_con_conteo_verificados_y_ejemplos() -> None:
    answer, _ = ask("¿Qué colegios hay en El Tintal?")
    assert answer.texto == ("En Centros Educativos hay 5 registros (2 verificados). "
                            "Por ejemplo: Colegio Alfa, Jardín Beta y IED Gamma.")
    assert [a.ruta for a in answer.acciones] == ["/categorias/centros-educativos"]
    assert (answer.modelo, answer.expresion, len(answer.datos)) == ("analitico", "wave", 3)
    empty, _ = ask("colegios", empty=True)
    assert empty.texto == "En Centros Educativos todavía no hay registros cargados."


def test_robos_avisa_sin_alarmar() -> None:
    answer, _ = ask("robos en el barrio")
    assert answer.expresion == "alert" and "llama al 123" in answer.texto


def test_mejor_calificado_con_y_sin_calificaciones() -> None:
    answer, tools = ask("¿Cuál es la barbería mejor calificada?")
    assert answer.texto == ("Lo mejor calificado en Barberías es Barbería Kings: "
                            "4,25 de 5 estrellas con 8 calificaciones.")
    assert answer.expresion == "jump" and tools.calls == [("best", "barberias")]
    empty, _ = ask("the best vet", "en", empty=True)
    assert empty.texto == "There are no ratings in Veterinary Clinics yet. You can be the first to rate."


def test_cercania_usa_la_ubicacion_o_el_centro_del_barrio() -> None:
    answer, tools = ask("¿Qué queda más cerca?", lon=-74.15, lat=4.65)
    assert answer.texto == ("Cerca de tu ubicación están: Parque El Tintal (73 m) "
                            "y Cancha de fútbol (1.093 m).")
    assert tools.calls == [("nearest", -74.15, 4.65, None)]
    assert len(answer.acciones) == 2
    empty, tools = ask("parks nearby", "en", empty=True)
    assert empty.texto == "I found no places in Green Areas within 1.5 km of the center of El Tintal."
    assert tools.calls == [("nearest", -74.16, 4.64, "zonas-verdes")]


def test_estadisticas_globales_y_por_modulo() -> None:
    answer, _ = ask("¿Cuántos lugares hay?")
    assert answer.texto.startswith("La plataforma tiene 4.183 registros en 14 módulos y 12 calificaciones.")
    assert "Datos Catastrales (3.706)" in answer.texto
    per_module, _ = ask("how many schools", "en")
    assert per_module.texto == "Schools has 5 records, 2 of them verified."


def test_historia_solo_con_hitos_oficiales_y_localidad() -> None:
    answer, _ = ask("cuéntame la historia")
    assert "1963: De Techo a Ciudad Kennedy y 1967" in answer.texto and "1959" not in answer.texto
    assert answer.acciones[0].ruta == "/historia"
    assert ask("historia", empty=True)[0].texto == "La historia del barrio todavía no está cargada."
    locality, _ = ask("Kennedy locality info", "en")
    assert locality.texto == "El Tintal is in the Kennedy Locality: 1,104,934 residents and 38.21 km²."
    assert ask("localidad", empty=True)[0].intent == "localidad"


def test_conversacion_con_sugerencias() -> None:
    hello, _ = ask("hola")
    assert hello.expresion == "wave" and len(hello.sugerencias) == 5
    contact, _ = ask("whatsapp de Marie")
    assert "313 259 6937" in contact.texto and contact.acciones[0].ruta == "/creadora"
    assert contact.sugerencias == ()
    lost, _ = ask("zzz", "en")
    assert lost.intent == "desconocido" and lost.expresion == "sad" and lost.texto.startswith("I didn't")
    assert ask("mapa 3d")[0].acciones[0].ruta == "/mapa"
