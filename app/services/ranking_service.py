"""Ranking global entre módulos: mejor promedio primero, desempate por número de votos."""

from collections.abc import Callable

from app.repositories.engagement_interfaces import RatingRepository
from app.schemas.engagement import RankingItem

Labeler = Callable[[str, int], str | None]


class GlobalRankingService:
    def __init__(self, ratings: RatingRepository, label: Labeler) -> None:
        self._ratings = ratings
        self._label = label

    def top(self, limit: int) -> list[RankingItem]:
        """Omite filas de módulos o lugares que ya no existen."""
        out = []
        for row in self._ratings.ranking(None, limit):
            name = self._label(row.categoria_slug, row.objeto_id)
            if name is not None:
                out.append(RankingItem(categoria_slug=row.categoria_slug, objeto_id=row.objeto_id,
                                       nombre=name, promedio=round(float(row.promedio), 2),
                                       total=row.total))
        return out
