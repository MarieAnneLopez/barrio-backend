"""Fixtures comunes: app real con PostGIS de docker compose y sondas falsas.

Cliente: httpx.AsyncClient + ASGITransport (§8), sin el TestClient de Starlette.
"""

from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db_probe
from app.core.exceptions import DatabaseUnavailableError
from app.main import create_app


class FakeProbe:
    """Sonda en memoria: responde una versión o simula la base caída."""

    def __init__(self, version: str | None = "3.4 USE_GEOS=1") -> None:
        self.version = version

    def postgis_version(self) -> str:
        if self.version is None:
            raise DatabaseUnavailableError()
        return self.version


def make_client(app: FastAPI, raise_app_exceptions: bool = True) -> AsyncClient:
    transport = ASGITransport(app=app, raise_app_exceptions=raise_app_exceptions)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with make_client(app) as http:
        yield http


@pytest.fixture
async def client_db_down(app: FastAPI) -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_db_probe] = lambda: FakeProbe(version=None)
    async with make_client(app) as http:
        yield http
    app.dependency_overrides.clear()
