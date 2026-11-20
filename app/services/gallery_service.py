"""Galería General (D66): las fotos de los 14 módulos con el nombre de su lugar."""

from math import ceil

from app.repositories.engagement_interfaces import GalleryRepository
from app.schemas.crud import PageOut
from app.schemas.engagement import FotoOut, GaleriaItem


class GlobalGalleryService:
    def __init__(self, photos: GalleryRepository) -> None:
        self._photos = photos

    def page(self, page: int, size: int) -> PageOut[GaleriaItem]:
        rows, total = self._photos.page((page - 1) * size, size)
        items = [GaleriaItem(**FotoOut.model_validate(row).model_dump(), categoria_slug=row.categoria_slug,
                             objeto_id=row.objeto_id, nombre=name) for row, name in rows]
        return PageOut(items=items, total=total, page=page, size=size, pages=ceil(total / size))
