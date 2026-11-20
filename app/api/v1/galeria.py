"""Galería General: todas las fotos de los lugares, con autor, licencia y lugar (D66)."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import SessionDep
from app.repositories.gallery_repository import SqlGalleryRepository
from app.schemas.crud import PageOut
from app.schemas.engagement import GaleriaItem
from app.services.gallery_service import GlobalGalleryService

router = APIRouter(tags=["galeria"])


def get_gallery_service(session: SessionDep) -> GlobalGalleryService:
    return GlobalGalleryService(SqlGalleryRepository(session))


@router.get("/fotos", response_model=PageOut[GaleriaItem])
def gallery(service: Annotated[GlobalGalleryService, Depends(get_gallery_service)],
            page: Annotated[int, Query(ge=1)] = 1,
            size: Annotated[int, Query(ge=1, le=100)] = 60) -> Any:
    return service.page(page, size)
