"""Cercanía (ST_DWithin) y estadísticas de calidad de datos de un módulo (H18)."""

from typing import Any

from app.repositories.engagement_interfaces import GeoInsightsRepository, RatingRepository
from app.schemas.engagement import Cercano, Estadisticas
from app.services.crud_service import CrudService


class GeoInsightsService:
    def __init__(self, slug: str, geo: GeoInsightsRepository, ratings: RatingRepository,
                 items: CrudService[Any]) -> None:
        self._slug = slug
        self._geo = geo
        self._ratings = ratings
        self._items = items

    def nearby(self, lon: float, lat: float, radius_m: float, limit: int) -> list[Cercano]:
        return [Cercano(distancia_m=d, item=self._items.get(i).model_dump(mode="json"))
                for i, d in self._geo.nearby(lon, lat, radius_m, limit)]

    def stats(self) -> Estadisticas:
        total, verified, examples = self._geo.counts()
        promedio, _, rated = self._ratings.summary(self._slug)
        return Estadisticas(total=total, verificados=verified, por_verificar=total - verified,
                            ejemplos=examples, calificados=rated, promedio_estrellas=promedio)
