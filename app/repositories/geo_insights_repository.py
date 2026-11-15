"""Consultas espaciales y de calidad de datos de un módulo: cercanía y conteos."""

from geoalchemy2 import Geography
from sqlalchemy import Float, cast, func, select
from sqlalchemy.orm import Session

from app.models.base import SRID, Base
from app.models.mixins import published

EXAMPLE_REF = "dato de ejemplo"


class SqlGeoInsightsRepository:
    def __init__(self, session: Session, model: type[Base]) -> None:
        self._session = session
        self._model = model

    def nearby(self, lon: float, lat: float, radius_m: float, limit: int) -> list[tuple[int, float]]:
        """(id, distancia en metros) dentro del radio, del más cercano al más lejano.

        ST_DWithin sobre geography: el radio está en metros reales, no en grados.
        """
        m = self._model
        here = cast(func.ST_SetSRID(func.ST_MakePoint(lon, lat), SRID), Geography)
        geog = cast(m.geom, Geography)  # type: ignore[attr-defined]
        distance = cast(func.ST_Distance(geog, here), Float).label("d")
        stmt = (select(m.id, distance)  # type: ignore[attr-defined]
                .where(m.geom.is_not(None), func.ST_DWithin(geog, here, radius_m))  # type: ignore[attr-defined]
                .where(*_visible(m))
                .order_by(distance, m.id).limit(limit))  # type: ignore[attr-defined]
        return [(row.id, round(row.d, 1)) for row in self._session.execute(stmt)]

    def counts(self) -> tuple[int, int, int]:
        """(total, verificados, datos de ejemplo)."""
        m = self._model
        stmt = select(func.count(), func.count().filter(m.verified.is_(True)),  # type: ignore[attr-defined]
                      func.count().filter(m.source_ref == EXAMPLE_REF)).where(*_visible(m))  # type: ignore[attr-defined]
        total, verified, examples = self._session.execute(stmt).one()
        return total, verified, examples


def _visible(model: type[Base]) -> tuple[object, ...]:
    """Filtro de publicados (H35) como argumentos de where(); vacío si no aplica."""
    condition = published(model)
    return () if condition is None else (condition,)
