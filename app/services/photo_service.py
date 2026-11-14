"""Galería de cada lugar: fotos locales con autor y licencia (§11.3 punto 4)."""

from typing import Any

from app.core.exceptions import AppError
from app.repositories.engagement_interfaces import PhotoRepository
from app.schemas.engagement import FotoIn, FotoOut
from app.services.crud_service import CrudService


class PhotoNotFoundError(AppError):
    def __init__(self, foto_id: int) -> None:
        super().__init__("NOT_FOUND", f"No existe la foto {foto_id} en este lugar", 404)


class PhotoService:
    def __init__(self, slug: str, photos: PhotoRepository, items: CrudService[Any]) -> None:
        self._slug = slug
        self._photos = photos
        self._items = items

    def list(self, objeto_id: int) -> list[FotoOut]:
        self._items.get(objeto_id)
        return [FotoOut.model_validate(p) for p in self._photos.list(self._slug, objeto_id)]

    def add(self, objeto_id: int, payload: FotoIn) -> FotoOut:
        self._items.get(objeto_id)
        return FotoOut.model_validate(self._photos.add(self._slug, objeto_id, payload.model_dump()))

    def remove(self, objeto_id: int, foto_id: int) -> None:
        if not self._photos.remove(self._slug, objeto_id, foto_id):
            raise PhotoNotFoundError(foto_id)
