"""/api/v1/auth: login, registro, sesión actual, cierre y cookie segura (H21, D58)."""

from collections.abc import Iterator

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.api.v1.auth import get_limiter
from app.models.usuario import Usuario
from tests.api.auth_helpers import PASSWORD, login, make_user

AUTH = "/api/v1/auth"


@pytest.fixture(autouse=True)
def fresh_limiter() -> Iterator[None]:
    get_limiter.cache_clear()
    yield
    get_limiter.cache_clear()


async def test_login_abre_sesion_con_cookie_httponly(client: AsyncClient, db_session: Session) -> None:
    make_user(db_session, "admin@prueba.co", rol="admin")

    response = await client.post(f"{AUTH}/login", json={"email": " ADMIN@prueba.co ", "password": PASSWORD})

    assert response.status_code == 200
    body = response.json()
    assert body["usuario"]["rol"] == "admin" and body["expires_in"] == 3600
    assert "password" not in str(body) and "token" not in str(body)
    cookie = response.headers["set-cookie"].lower()
    assert "mm_session=" in cookie and "httponly" in cookie and "samesite=strict" in cookie
    assert "path=/api" in cookie
    me = await client.get(f"{AUTH}/me")
    assert me.json()["email"] == "admin@prueba.co"
    assert (await client.get(f"{AUTH}/session")).json()["usuario"]["rol"] == "admin"


@pytest.mark.parametrize("email, password", [("admin@prueba.co", "otra-clave-999"),
                                             ("nadie@prueba.co", PASSWORD),
                                             ("inactivo@prueba.co", PASSWORD)])
async def test_credenciales_invalidas_dan_el_mismo_401(client: AsyncClient, db_session: Session,
                                                     email: str, password: str) -> None:
    make_user(db_session, "admin@prueba.co", rol="admin")
    make_user(db_session, "inactivo@prueba.co", activo=False)

    response = await client.post(f"{AUTH}/login", json={"email": email, "password": password})

    assert response.status_code == 401
    assert response.json()["error"] == {"code": "INVALID_CREDENTIALS", "message": "Correo o contraseña incorrectos"}
    assert "set-cookie" not in response.headers


async def test_registro_crea_visitante_y_rechaza_correo_repetido(client: AsyncClient,
                                                                 db_session: Session) -> None:
    data = {"nombre": "Vecina", "email": "vecina@prueba.co", "password": "una-clave-larga"}

    created = await client.post(f"{AUTH}/register", json=data)
    again = await client.post(f"{AUTH}/register", json={**data, "email": "VECINA@prueba.co"})

    assert created.status_code == 201 and created.json()["usuario"]["rol"] == "visitante"
    assert again.status_code == 409 and again.json()["error"]["code"] == "EMAIL_TAKEN"
    stored = db_session.query(Usuario).one()
    assert stored.password_hash.startswith("$2b$12$") and "una-clave-larga" not in stored.password_hash


@pytest.mark.parametrize("payload", [
    {"nombre": "X", "email": "x@prueba.co", "password": "corta"},
    {"nombre": "X", "email": "sin-arroba", "password": "una-clave-larga"},
    {"nombre": "X", "email": "x@prueba.co", "password": "ñ" * 40},
    {"nombre": "X", "email": "x@prueba.co", "password": "una-clave-larga", "rol": "admin"},
])
async def test_registro_valida_entrada_y_no_acepta_rol(client: AsyncClient, payload: dict[str, str]) -> None:
    response = await client.post(f"{AUTH}/register", json=payload)
    assert response.status_code == 422


async def test_logout_borra_la_cookie(client: AsyncClient, db_session: Session) -> None:
    make_user(db_session, "v@prueba.co")
    assert await login(client, "v@prueba.co") == 200

    response = await client.post(f"{AUTH}/logout")

    assert response.status_code == 204 and 'mm_session=""' in response.headers["set-cookie"]
    assert (await client.get(f"{AUTH}/me")).status_code == 401
    assert (await client.get(f"{AUTH}/session")).json() == {"usuario": None}


async def test_limite_de_intentos_fallidos(client: AsyncClient, db_session: Session) -> None:
    make_user(db_session, "v@prueba.co")
    codes = [await login(client, "v@prueba.co", "clave-errada-00") for _ in range(10)]

    blocked = await client.post(f"{AUTH}/login", json={"email": "v@prueba.co", "password": PASSWORD})

    assert set(codes) == {401}
    assert blocked.status_code == 429 and blocked.json()["error"]["code"] == "TOO_MANY_ATTEMPTS"
