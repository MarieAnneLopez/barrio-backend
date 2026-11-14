"""CrudRouterFactory de extremo a extremo (Centros Educativos sobre barrio_test)."""

import pytest
from sqlalchemy.orm import Session

from tests.api.crud_app import BASE, POINT, colegio, crud_app
from tests.conftest import make_client

pytestmark = pytest.mark.usefixtures("db_session")  # vacía las tablas al terminar


async def test_las_escrituras_exigen_sesion_de_admin() -> None:
    async with make_client(crud_app(as_admin=False)) as http:
        created = await http.post(BASE, json=colegio())
        patched = await http.patch(f"{BASE}/1", json={"nombre": "X"})
        deleted = await http.delete(f"{BASE}/1")

    assert {created.status_code, patched.status_code, deleted.status_code} == {401}
    assert created.json()["error"]["code"] == "AUTH_REQUIRED"


async def test_crud_completo_como_admin() -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        created = await http.post(BASE, json=colegio(telefono="601 234 5678"))
        item_id = created.json()["id"]
        detail = await http.get(f"{BASE}/{item_id}")
        patched = await http.patch(f"{BASE}/{item_id}", json={"jornadas": "mañana, tarde"})
        deleted = await http.delete(f"{BASE}/{item_id}")
        missing = await http.get(f"{BASE}/{item_id}")

    assert created.status_code == 201
    assert detail.json()["geometry"] == POINT and detail.json()["verified"] is False
    assert patched.json()["jornadas"] == "mañana, tarde"
    assert patched.json()["nombre"] == "Colegio Distrital Alfa"
    assert deleted.status_code == 204
    assert missing.status_code == 404 and missing.json()["error"]["code"] == "NOT_FOUND"


async def test_lista_paginada_busqueda_filtros_y_orden() -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        for nombre, tipo in [("Jardín Sol", "jardin"), ("Colegio Luna", "colegio"),
                             ("Colegio Estrella", "colegio")]:
            await http.post(BASE, json={**colegio(nombre), "tipo": tipo})
        page = await http.get(BASE, params={"tipo": "colegio", "sort": "-nombre", "size": 1})
        search = await http.get(BASE, params={"q": "sol"})

    body = page.json()
    assert (body["total"], body["pages"], body["size"]) == (2, 2, 1)
    assert body["items"][0]["nombre"] == "Colegio Luna"
    assert [i["nombre"] for i in search.json()["items"]] == ["Jardín Sol"]


async def test_geojson_es_ruta_estatica_antes_del_id() -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        await http.post(BASE, json=colegio())
        response = await http.get(f"{BASE}/geojson")

    body = response.json()
    assert response.status_code == 200 and body["type"] == "FeatureCollection"
    feature = body["features"][0]
    assert feature["geometry"] == POINT and feature["properties"]["nombre"] == "Colegio Distrital Alfa"


@pytest.mark.parametrize(
    "payload",
    [
        colegio(tipo="hospital"),
        colegio(geometry={"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}),
        colegio(telefono="llamar ya"),
        colegio(id=99),  # asignación masiva de campos del servidor
    ],
)
async def test_valida_la_entrada_con_422(payload: dict) -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        response = await http.post(BASE, json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_parametros_de_lista_invalidos(db_session: Session) -> None:
    async with make_client(crud_app(as_admin=False)) as http:
        too_big = await http.get(BASE, params={"size": 500})
        bad_sort = await http.get(BASE, params={"sort": "telefono"})
        bad_filter = await http.get(BASE, params={"color": "azul"})

    assert {too_big.status_code, bad_sort.status_code, bad_filter.status_code} == {422}
