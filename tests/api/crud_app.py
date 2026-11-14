"""App real (el registro ya expone Centros Educativos vía CrudRouterFactory)."""

from typing import Any

from fastapi import FastAPI

from app.api.guards import require_admin
from app.main import create_app

BASE = "/api/v1/centros-educativos"
POINT = {"type": "Point", "coordinates": [-74.1547809, 4.6430253]}


def crud_app(as_admin: bool) -> FastAPI:
    app = create_app()
    if as_admin:
        app.dependency_overrides[require_admin] = lambda: None
    return app


def colegio(nombre: str = "Colegio Distrital Alfa", **extra: Any) -> dict[str, Any]:
    return {"nombre": nombre, "tipo": "colegio", "caracter": "publico", "geometry": POINT, **extra}
