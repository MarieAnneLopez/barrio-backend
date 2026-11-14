"""H18: galería de cada lugar y limpieza al borrar el lugar."""

import pytest

from tests.api.crud_app import crud_app
from tests.api.test_engagement import BASE, barberia
from tests.conftest import make_client

pytestmark = pytest.mark.usefixtures("db_session")
FOTO = {"url": "/assets/photos/barberia-alfa.webp", "alt_text": "Fachada de la barbería", "autor": "Marie"}


async def test_galeria_solo_rutas_locales_y_admin() -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        item = await barberia(http, "Alfa")
        added = await http.post(f"{BASE}/{item}/fotos", json=FOTO)
        external = await http.post(f"{BASE}/{item}/fotos", json={**FOTO, "url": "https://x.com/a.jpg"})
        listed = (await http.get(f"{BASE}/{item}/fotos")).json()
        removed = await http.delete(f"{BASE}/{item}/fotos/{added.json()['id']}")
        again = await http.delete(f"{BASE}/{item}/fotos/{added.json()['id']}")
    async with make_client(crud_app(as_admin=False)) as http:
        anon = await http.post(f"{BASE}/{item}/fotos", json=FOTO)

    assert added.status_code == 201 and listed[0]["url"] == FOTO["url"]
    assert external.status_code == 422
    assert (removed.status_code, again.status_code, anon.status_code) == (204, 404, 401)


async def test_borrar_un_lugar_borra_sus_calificaciones_y_fotos() -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        item = await barberia(http, "Alfa")
        await http.post(f"{BASE}/{item}/calificaciones", json={"estrellas": 5})
        await http.post(f"{BASE}/{item}/fotos", json=FOTO)
        await http.delete(f"{BASE}/{item}")
        ranking = (await http.get("/api/v1/ranking")).json()
        stats = (await http.get(f"{BASE}/stats")).json()

    assert ranking == [] and stats["calificados"] == 0
