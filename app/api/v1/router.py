"""Router raíz de /api/v1: aquí se registran los routers de cada módulo."""

from fastapi import APIRouter

from app.api.v1 import barrio, health
from app.api.v1.router_factory import CrudRouterFactory
from app.modules.registry import MODULES

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(barrio.router)
for spec in MODULES:
    api_router.include_router(CrudRouterFactory(spec).build())
