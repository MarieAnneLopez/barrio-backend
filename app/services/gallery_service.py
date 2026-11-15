"""Galería General (D66): las fotos de los 14 módulos con el nombre de su lugar."""

from math import ceil

from app.repositories.engagement_interfaces import GalleryRepository
from app.schemas.crud import PageOut
from app.schemas.engagement import FotoOut, GaleriaItem
from app.services.ranking_service import Labeler


class GlobalGalleryService:
    def __init__(self, photos: GalleryRepository, label: Labeler) -> None:
        self._photos = photos
        self._label = label

    def page(self, page: int, size: int) -> PageOut[GaleriaItem]:
        """Omite fotos de lugares que ya no existen (no deberían quedar: se borran con el lugar)."""
        rows, total = self._photos.page((page - 1) * size, size)
        items = []
        for row in rows:
            name = self._label(row.categoria_slug, row.objeto_id)
            if name is not None:
                base = FotoOut.model_validate(row).model_dump()
                items.append(GaleriaItem(**base, categoria_slug=row.categoria_slug,
                                         objeto_id=row.objeto_id, nombre=name))
        return PageOut(items=items, total=total, page=page, size=size, pages=ceil(total / size))
