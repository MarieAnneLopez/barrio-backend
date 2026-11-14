"""RateableService: calificaciones y ranking de un módulo (§11.3 punto 5).

Solo se califica lo que existe: el objeto se consulta primero por el CRUD del
módulo (404 si no está). El promedio se copia a calificacion_promedio en los
módulos que tienen esa columna.
"""

from typing import Any

from app.repositories.engagement_interfaces import RatingRepository
from app.schemas.engagement import CalificacionIn, CalificacionOut, RankingItem, ResumenCalificaciones
from app.services.crud_service import CrudService


class RateableService:
    def __init__(self, slug: str, model: Any, label_field: str, ratings: RatingRepository,
                 items: CrudService[Any]) -> None:
        self._slug = slug
        self._model = model
        self._label = label_field
        self._ratings = ratings
        self._items = items

    def rate(self, objeto_id: int, payload: CalificacionIn, usuario_id: int | None = None) -> CalificacionOut:
        self._items.get(objeto_id)
        rating = self._ratings.add(self._slug, objeto_id, {**payload.model_dump(), "usuario_id": usuario_id})
        self._ratings.sync_average(self._model, self._slug, objeto_id)
        return CalificacionOut.model_validate(rating)

    def summary(self, objeto_id: int, limit: int = 20) -> ResumenCalificaciones:
        self._items.get(objeto_id)
        promedio, total, _ = self._ratings.summary(self._slug, objeto_id)
        items = [CalificacionOut.model_validate(r)
                 for r in self._ratings.latest(self._slug, objeto_id, limit)]
        return ResumenCalificaciones(promedio=promedio, total=total, items=items)

    def ranking(self, limit: int) -> list[RankingItem]:
        out = []
        for row in self._ratings.ranking(self._slug, limit):
            item = self._items.get(row.objeto_id)
            out.append(RankingItem(categoria_slug=self._slug, objeto_id=row.objeto_id,
                                   nombre=str(getattr(item, self._label)),
                                   promedio=round(float(row.promedio), 2), total=row.total))
        return out
