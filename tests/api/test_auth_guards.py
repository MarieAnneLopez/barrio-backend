"""Roles sobre las escrituras (H21, D58): sin sesión 401, visitante 403, admin pasa."""

from datetime import UTC, datetime, timedelta

import jwt
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import ALGORITHM, create_access_token
from app.models.calificacion import Calificacion
from tests.api.auth_helpers import login, make_user
from tests.api.crud_app import BASE, colegio


async def test_sin_sesion_las_escrituras_responden_401(client: AsyncClient) -> None:
    response = await client.post(BASE, json=colegio())
    assert response.status_code == 401 and response.json()["error"]["code"] == "AUTH_REQUIRED"


async def test_visitante_no_escribe_en_el_crud_pero_si_califica(client: AsyncClient,
                                                                 db_session: Session) -> None:
    admin = make_user(db_session, "admin@prueba.co", rol="admin")
    visitante = make_user(db_session, "v@prueba.co")
    assert await login(client, admin.email) == 200
    item = (await client.post(BASE, json=colegio())).json()["id"]
    await client.post("/api/v1/auth/logout")
    assert await login(client, visitante.email) == 200

    create = await client.post(BASE, json=colegio("Otro colegio"))
    delete = await client.delete(f"{BASE}/{item}")
    rate = await client.post(f"{BASE}/{item}/calificaciones", json={"estrellas": 4})

    assert create.status_code == 403 and create.json()["error"]["code"] == "FORBIDDEN"
    assert delete.status_code == 403
    assert rate.status_code == 201
    stored = db_session.scalar(select(Calificacion))
    assert stored is not None and stored.usuario_id == visitante.id


async def test_admin_crea_edita_y_borra(client: AsyncClient, db_session: Session) -> None:
    make_user(db_session, "admin@prueba.co", rol="admin")
    assert await login(client, "admin@prueba.co") == 200

    created = await client.post(BASE, json=colegio())
    item = created.json()["id"]
    patched = await client.patch(f"{BASE}/{item}", json={"nombre": "Colegio Beta"})
    deleted = await client.delete(f"{BASE}/{item}")

    assert (created.status_code, patched.status_code, deleted.status_code) == (201, 200, 204)


async def test_cuenta_desactivada_pierde_la_sesion(client: AsyncClient, db_session: Session) -> None:
    admin = make_user(db_session, "admin@prueba.co", rol="admin")
    assert await login(client, admin.email) == 200
    admin.activo = False
    db_session.commit()

    assert (await client.post(BASE, json=colegio())).status_code == 401


async def test_tokens_vencidos_alterados_o_de_otra_clave_no_valen(client: AsyncClient,
                                                                  db_session: Session) -> None:
    admin = make_user(db_session, "admin@prueba.co", rol="admin")
    old = create_access_token(admin.id, now=datetime.now(UTC) - timedelta(hours=2))
    good = create_access_token(admin.id)
    forged = jwt.encode({"sub": str(admin.id), "iat": datetime.now(UTC),
                         "exp": datetime.now(UTC) + timedelta(hours=1)}, "x" * 40, algorithm=ALGORITHM)
    unsigned = jwt.encode({"sub": str(admin.id)}, None, algorithm="none")

    for token in (old, good[:-2] + "xx", forged, unsigned, "basura"):
        client.cookies.set("mm_session", token, path="/api")
        assert (await client.post(BASE, json=colegio())).status_code == 401
    client.cookies.set("mm_session", good, path="/api")
    assert (await client.post(BASE, json=colegio())).status_code == 201
