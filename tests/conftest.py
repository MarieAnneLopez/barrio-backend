"""Fixtures comunes: app real con PostGIS de docker compose y sondas falsas.

Cliente: httpx.AsyncClient + ASGITransport (§8), sin el TestClient de Starlette.
Las pruebas usan su propia base (barrio_test), nunca la de desarrollo.
"""

import os

os.environ["POSTGRES_DB"] = "barrio_test"  # antes de importar app: get_settings está cacheado

from collections.abc import AsyncIterator, Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.api.deps import get_db_probe  # noqa: E402
from app.core.exceptions import DatabaseUnavailableError  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

import app.models as _models  # noqa: E402, F401  (registra las tablas)
from app.core.database import get_engine  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models.base import Base  # noqa: E402
from tests.db_setup import alembic, ensure_database  # noqa: E402

TEST_DB = os.environ["POSTGRES_DB"]


@pytest.fixture(scope="session", autouse=True)
def test_database() -> Iterator[None]:
    """Base de pruebas creada y migrada a head una vez por sesión."""
    ensure_database(TEST_DB)
    alembic("upgrade", "head")
    yield


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


@pytest.fixture
def db_session() -> Iterator[Session]:
    """Sesión real sobre barrio_test; al terminar vacía todas las tablas del proyecto."""
    engine = get_engine()
    with Session(engine) as session:
        yield session
    tables = ", ".join(f'"{name}"' for name in Base.metadata.tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
