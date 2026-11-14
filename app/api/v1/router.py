"""Router raíz de /api/v1: aquí se registran los routers de cada módulo."""

from fastapi import APIRouter

from app.api.v1 import barrio, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(barrio.router)
