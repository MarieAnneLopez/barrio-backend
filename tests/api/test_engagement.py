"""H18: cercanía con ST_DWithin, estadísticas, calificaciones y ranking."""

from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models import Barberia

from tests.api.crud_app import crud_app
from tests.api.module_payloads import payload
from tests.conftest import make_client

pytestmark = pytest.mark.usefixtures("db_session")
BASE = "/api/v1/barberias"
HERE = (-74.1547809, 4.6430253)


async def barberia(http: AsyncClient, nombre: str, lon: float = HERE[0], lat: float = HERE[1],
                   **extra: object) -> int:
    body = payload("barberias", nombre=nombre, **extra)
    body["geometry"] = {"type": "Point", "coordinates": [lon, lat]}
    return (await http.post(BASE, json=body)).json()["id"]


async def test_cercania_en_metros_reales_y_ordenada() -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        await barberia(http, "Lejos", lon=-74.1577659, lat=4.6540182)  # Ciudad Tintal, ≈ 1,3 km
        near = await barberia(http, "Cerca", lon=HERE[0] + 0.001)  # ≈ 111 m
        found = await http.get(f"{BASE}/cercania", params={"lon": HERE[0], "lat": HERE[1], "radio_m": 500})
        bad = await http.get(f"{BASE}/cercania", params={"lon": HERE[0], "lat": 95})

    [item] = found.json()
    assert item["item"]["id"] == near and 105 < item["distancia_m"] < 115
    assert bad.status_code == 422


async def test_stats_distingue_verificados_y_ejemplos() -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        await barberia(http, "Real", verified=True, source_type="osm", source_ref="osm/1")
        await barberia(http, "Ejemplo", source_ref="dato de ejemplo")
        stats = (await http.get(f"{BASE}/stats")).json()

    assert stats == {"total": 2, "verificados": 1, "por_verificar": 1, "ejemplos": 1,
                     "calificados": 0, "promedio_estrellas": None}


async def test_calificar_promedia_y_sincroniza_la_columna(db_session: Session) -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        item = await barberia(http, "Alfa")
        first = await http.post(f"{BASE}/{item}/calificaciones", json={"estrellas": 4.5, "comentario": "Buen corte"})
        await http.post(f"{BASE}/{item}/calificaciones", json={"estrellas": 3})
        summary = (await http.get(f"{BASE}/{item}/calificaciones")).json()

    assert first.status_code == 201 and first.json()["estrellas"] == 4.5
    assert (summary["promedio"], summary["total"]) == (3.75, 2)
    assert summary["items"][0]["estrellas"] == 3.0
    assert db_session.get(Barberia, item).calificacion_promedio == Decimal("3.8")  # type: ignore[union-attr]


@pytest.mark.parametrize("stars", [4.3, 5.5, -0.5])
async def test_estrellas_en_pasos_de_medio_punto(stars: float) -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        item = await barberia(http, "Alfa")
        response = await http.post(f"{BASE}/{item}/calificaciones", json={"estrellas": stars})

    assert response.status_code == 422


async def test_calificar_exige_sesion_y_objeto_existente() -> None:
    async with make_client(crud_app(as_admin=False)) as http:
        anon = await http.post(f"{BASE}/1/calificaciones", json={"estrellas": 4})
    async with make_client(crud_app(as_admin=True)) as http:
        missing = await http.post(f"{BASE}/999/calificaciones", json={"estrellas": 4})

    assert anon.status_code == 401 and missing.status_code == 404


async def test_ranking_por_modulo_y_global() -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        alfa, beta = await barberia(http, "Alfa"), await barberia(http, "Beta")
        vet = (await http.post("/api/v1/veterinarias", json=payload("veterinarias"))).json()["id"]
        for item, stars in [(alfa, 4), (alfa, 4), (beta, 5), (beta, 3)]:
            await http.post(f"{BASE}/{item}/calificaciones", json={"estrellas": stars})
        await http.post(f"/api/v1/veterinarias/{vet}/calificaciones", json={"estrellas": 5})
        local = (await http.get(f"{BASE}/ranking")).json()
        global_ = (await http.get("/api/v1/ranking", params={"limit": 3})).json()

    # Mismo promedio (4,0) y mismos votos: desempata el id más antiguo.
    assert [r["nombre"] for r in local] == ["Alfa", "Beta"]
    assert global_[0] == {"categoria_slug": "veterinarias", "objeto_id": vet,
                          "nombre": "Veterinaria Alfa", "promedio": 5.0, "total": 1}
