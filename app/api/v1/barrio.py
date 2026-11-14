"""GET /api/v1/barrio/poligono: límite de El Tintal para el mapa (maxBounds, D5)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_barrio_service
from app.schemas.barrio import BarrioPolygon
from app.services.barrio_service import BarrioService

router = APIRouter(prefix="/barrio", tags=["barrio"])


@router.get("/poligono", response_model=BarrioPolygon)
def poligono(service: Annotated[BarrioService, Depends(get_barrio_service)]) -> BarrioPolygon:
    return service.polygon()
