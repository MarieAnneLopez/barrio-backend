"""GET /api/v1/historia: línea de tiempo de El Tintal y Kennedy con sus fuentes (H20)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep
from app.core.config import get_settings
from app.repositories.historia_repository import SqlHistoriaRepository
from app.schemas.historia import HistoriaOut
from app.services.historia_service import HistoriaService

router = APIRouter(tags=["historia"])


def get_historia_service(session: SessionDep) -> HistoriaService:
    catalog = get_settings().seed_dir / "historia.json"
    return HistoriaService(SqlHistoriaRepository(session, catalog))


@router.get("/historia", response_model=HistoriaOut)
def historia(service: Annotated[HistoriaService, Depends(get_historia_service)]) -> HistoriaOut:
    return service.historia()
