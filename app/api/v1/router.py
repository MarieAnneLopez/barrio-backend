"""Router raíz de /api/v1: aquí se registran los routers de cada módulo.

Por módulo, primero los extras (rutas estáticas /cercania, /ranking, /stats) y
después el CRUD con /{item_id} (D10).
"""

from fastapi import APIRouter

from app.api.v1 import auth, barrio, health, historia, ranking
from app.api.v1.module_extras import ModuleExtrasFactory
from app.api.v1.router_factory import CrudRouterFactory
from app.modules.registry import MODULES

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(barrio.router)
api_router.include_router(ranking.router)
api_router.include_router(historia.router)
for spec in MODULES:
    api_router.include_router(ModuleExtrasFactory(spec).build())
    api_router.include_router(CrudRouterFactory(spec).build())
