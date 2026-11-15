"""Arreglos de la revisión de H30: límite de El Tintal en la API, base caída y /auth/me."""

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.exc import OperationalError

from app.api.v1.historia import get_historia_service
from tests.api.crud_app import BASE, colegio, crud_app
from tests.conftest import make_client

pytestmark = pytest.mark.usefixtures("db_session")
OUTSIDE = {"type": "Point", "coordinates": [-74.1347809, 4.6430253]}  # ≈ 2 km al este, fuera de UPZ 78 + 79


async def test_la_api_rechaza_geometrias_fuera_de_el_tintal() -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        rejected = await http.post(BASE, json=colegio(geometry=OUTSIDE))
        created = (await http.post(BASE, json=colegio())).json()
        moved = await http.patch(f"{BASE}/{created['id']}", json={"geometry": OUTSIDE})
        renamed = await http.patch(f"{BASE}/{created['id']}", json={"nombre": "Sin mover"})

    assert rejected.status_code == 422 and rejected.json()["error"]["code"] == "OUTSIDE_TINTAL"
    assert moved.status_code == 422 and renamed.status_code == 200


async def test_la_ficha_de_kennedy_no_tiene_ese_limite() -> None:
    kennedy = {"nombre_localidad": "Kennedy", "geometry": None}
    async with make_client(crud_app(as_admin=True)) as http:
        assert (await http.post("/api/v1/localidad", json=kennedy)).status_code == 201


async def test_base_caida_responde_503_con_formato_unico(app: FastAPI) -> None:
    def down() -> None:
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    app.dependency_overrides[get_historia_service] = down
    async with make_client(app, raise_app_exceptions=False) as http:
        response = await http.get("/api/v1/historia")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATABASE_UNAVAILABLE"


async def test_me_sin_sesion_pide_iniciarla(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Inicia sesión para continuar"
