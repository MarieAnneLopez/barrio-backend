"""POST /api/v1/chat y SqlBarrioTools sobre PostGIS (H22, D59)."""

from collections.abc import Iterator

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.api.v1.chat import get_chat_limiter
from app.core.database import get_engine
from etl import load_historia
from tests.api.crud_app import crud_app
from tests.conftest import make_client

pytestmark = pytest.mark.usefixtures("db_session")
CHAT = "/api/v1/chat"
HERE = [-74.1547809, 4.6430253]


@pytest.fixture(autouse=True)
def fresh_limiter() -> Iterator[None]:
    get_chat_limiter.cache_clear()
    yield
    get_chat_limiter.cache_clear()


async def test_colegios_cercania_ranking_e_historia_con_datos_reales(db_session: Session) -> None:
    load_historia.run(get_engine())
    async with make_client(crud_app(as_admin=True)) as http:
        # Al norte de la biblioteca: hacia el este se sale de El Tintal (la API lo rechaza).
        for nombre, lat in (("Colegio Alfa", HERE[1]), ("Colegio Beta", HERE[1] + 0.002)):
            body = {"nombre": nombre, "tipo": "colegio", "caracter": "publico",
                    "geometry": {"type": "Point", "coordinates": [HERE[0], lat]}}
            item = (await http.post("/api/v1/centros-educativos", json=body)).json()["id"]
        await http.post(f"/api/v1/centros-educativos/{item}/calificaciones", json={"estrellas": 4.5})

        listed = (await http.post(CHAT, json={"mensaje": "¿Qué colegios hay?"})).json()
        near = (await http.post(CHAT, json={"mensaje": "colegios cerca", "lon": HERE[0], "lat": HERE[1]})).json()
        best = (await http.post(CHAT, json={"mensaje": "the best school", "idioma": "en"})).json()
        history = (await http.post(CHAT, json={"mensaje": "historia", "ruta": "/historia"})).json()

    assert listed["texto"] == "En Centros Educativos hay 2 registros (0 verificados). Por ejemplo: Colegio Alfa y Colegio Beta."
    assert listed["acciones"] == [{"ruta": "/categorias/centros-educativos", "etiqueta": "Centros Educativos"}]
    assert near["texto"] == "Cerca de tu ubicación están: Colegio Alfa (0 m) y Colegio Beta (221 m)."
    assert best["texto"].startswith("The best-rated place in Schools is Colegio Beta: 4.5 out of 5")
    assert history["intent"] == "historia" and history["acciones"] == []  # ya está en /historia
    assert "1963: De Techo a Ciudad Kennedy" in history["texto"]


async def test_sin_datos_y_modelo_por_defecto(client: AsyncClient) -> None:
    body = (await client.post(CHAT, json={"mensaje": "¿Qué queda más cerca?"})).json()
    assert body["texto"] == "No encontré lugares a menos de 1,5 km del centro de El Tintal."
    assert (body["modelo"], body["experto"], body["expresion"]) == ("analitico", None, "idle")
    stats = (await client.post(CHAT, json={"mensaje": "¿cuántos lugares hay?"})).json()
    assert stats["texto"].startswith("La plataforma tiene 0 registros")
    kennedy = (await client.post(CHAT, json={"mensaje": "localidad"})).json()
    assert kennedy["texto"] == "La historia del barrio todavía no está cargada."
    # H36: sin proveedor externo configurado, el chat no avisa de Gemini.
    assert (await client.get(f"{CHAT}/estado")).json() == {"proveedor": None}


@pytest.mark.parametrize("payload", [
    {"mensaje": ""}, {"mensaje": "x" * 501}, {"mensaje": "hola", "lon": -74.1},
    {"mensaje": "hola", "idioma": "fr"}, {"mensaje": "hola", "ruta": "javascript:alert(1)"},
    {"mensaje": "hola", "rol": "admin"},
])
async def test_valida_la_entrada(client: AsyncClient, payload: dict[str, object]) -> None:
    assert (await client.post(CHAT, json=payload)).status_code == 422


async def test_limite_de_mensajes_por_minuto(client: AsyncClient) -> None:
    codes = [(await client.post(CHAT, json={"mensaje": "hola"})).status_code for _ in range(31)]
    assert codes[:30] == [200] * 30 and codes[30] == 429
