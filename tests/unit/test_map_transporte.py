"""Estaciones y paraderos: tipo por red/nombre, rutas desde relaciones y sin duplicados."""

from etl.modules import transporte


def _el(i: int, **tags: str) -> dict:
    return {"type": "node", "id": i, "tags": tags, "lat": 4.65, "lon": -74.15}


def _feature(i: int, **tags: str) -> dict:
    props, _ = transporte.map_element(_el(i, **tags))
    return {"type": "Feature", "properties": props, "geometry": None}


def test_tipos_troncal_alimentador_y_sitp() -> None:
    troncal = transporte.map_element(_el(1, name="Portal Américas", network="TransMilenio"))[0]
    alim = transporte.map_element(_el(2, name="Tintal", network="TransMilenio Alimentador"))[0]
    sitp = transporte.map_element(_el(3, name="Biblioteca El Tintal", highway="bus_stop"))[0]

    assert troncal and alim and sitp
    assert (troncal["tipo"], alim["tipo"], sitp["tipo"]) == ("troncal", "alimentador", "sitp")


def test_paradero_sin_nombre_propio_se_omite() -> None:
    assert transporte.map_element(_el(4, highway="bus_stop"))[0] is None
    assert transporte.map_element(_el(5, name="SITP"))[1] == "paradero sin nombre propio"


def test_lineas_de_route_ref_y_de_las_relaciones() -> None:
    class FakeOverpass:
        def query(self, ql: str) -> dict:
            assert 'rel(bn.s)["route"="bus"]' in ql
            return {"elements": [{"type": "relation", "tags": {"ref": "8-3"},
                                  "members": [{"type": "node", "ref": 6}]}]}

    [element] = transporte.enrich(FakeOverpass(), [_el(6, name="Tintalá", route_ref="E44")])
    props, _ = transporte.map_element(element)

    assert props is not None and props["lineas"] == "8-3, E44"


def test_finalize_deja_la_estacion_y_quita_duplicados() -> None:
    platform = _feature(7, name="Tintal Plaza", public_transport="platform")
    station = _feature(8, name="Tintal Plaza", public_transport="station")
    other = _feature(9, name="Primavera", highway="bus_stop")

    result = transporte.finalize([platform, station, other])

    assert [f["properties"]["source_ref"][-6:] for f in result] == ["node/8", "node/9"]
    assert all("_rank" not in f["properties"] for f in result)
