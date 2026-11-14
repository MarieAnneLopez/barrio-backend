"""Formato único de error en toda la API."""

from fastapi import FastAPI
from httpx import AsyncClient

from app.core.exceptions import AppError
from tests.conftest import make_client


async def test_ruta_inexistente_usa_el_formato_de_error(client: AsyncClient) -> None:
    response = await client.get("/api/v1/no-existe")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


async def test_validacion_devuelve_422_con_detalles(app: FastAPI) -> None:
    @app.get("/prueba/numero")
    def numero(n: int) -> dict[str, int]:
        return {"n": n}

    async with make_client(app) as http:
        response = await http.get("/prueba/numero", params={"n": "abc"})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"][0]["loc"] == ["query", "n"]


async def test_error_de_dominio_conserva_codigo_y_estado(app: FastAPI) -> None:
    @app.get("/prueba/conflicto")
    def conflicto() -> None:
        raise AppError("DUPLICADO", "Ya existe", 409, {"campo": "nombre"})

    async with make_client(app) as http:
        response = await http.get("/prueba/conflicto")

    assert response.status_code == 409
    assert response.json() == {
        "error": {"code": "DUPLICADO", "message": "Ya existe", "details": {"campo": "nombre"}}
    }


async def test_error_no_controlado_no_filtra_detalles(app: FastAPI) -> None:
    @app.get("/prueba/fallo")
    def fallo() -> None:
        raise RuntimeError("secreto interno: conexión a 10.0.0.5")

    async with make_client(app, raise_app_exceptions=False) as http:
        response = await http.get("/prueba/fallo")

    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "INTERNAL_ERROR", "message": "Error interno del servidor"}
    }
    assert "secreto" not in response.text
