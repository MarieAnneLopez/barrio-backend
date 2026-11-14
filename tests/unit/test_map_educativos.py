"""Mapeo OSM → Centros Educativos: sin inventar el carácter público/privado."""

from etl.modules.educativos import map_school


def _el(amenity: str, name: str | None, **tags: str) -> dict:
    base = {"amenity": amenity, **({"name": name} if name else {}), **tags}
    return {"type": "way", "id": 7, "tags": base, "center": {"lat": 4.65, "lon": -74.15}}


def test_publico_explicito_queda_verificado() -> None:
    record, reason = map_school(_el("kindergarten", "Jardín Infantil El Caracol", **{"operator:type": "public"}))

    assert reason is None and record is not None
    expected = {"tipo": "jardin", "caracter": "publico", "verified": True}
    assert record["properties"].items() >= expected.items()
    assert record["geometry"] == {"type": "Point", "coordinates": [-74.15, 4.65]}
    assert record["properties"]["source_ref"] == "https://www.openstreetmap.org/way/7"


def test_ied_se_infiere_publico_pero_por_verificar() -> None:
    record, _ = map_school(_el("school", "IED Saludcoop Calandaima"))

    assert record is not None
    assert record["properties"]["caracter"] == "publico"
    assert record["properties"]["verified"] is False


def test_sin_caracter_determinable_se_omite_con_motivo() -> None:
    record, reason = map_school(_el("school", "Gimnasio Moderno San Francisco"))

    assert record is None and reason == "carácter público/privado desconocido"


def test_sin_nombre_se_omite() -> None:
    assert map_school(_el("school", None)) == (None, "sin nombre")


def test_college_llamado_colegio_es_colegio() -> None:
    record, _ = map_school(_el("college", "Colegio Codema IED"))

    assert record is not None and record["properties"]["tipo"] == "colegio"


def test_direccion_desde_addr() -> None:
    element = _el("school", "IED Gabriel Betancourt Mejia Sede A",
                  **{"addr:street": "Carrera 87A", "addr:housenumber": "6-21"})
    record, _ = map_school(element)

    assert record is not None and record["properties"]["direccion"] == "Carrera 87A 6-21"
