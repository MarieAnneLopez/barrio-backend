"""Herramientas del chat sobre PostGIS: conteos, ranking, cercanía, historia y localidad.

Reusa los repositorios de los módulos (conteos, cercanía con ST_DWithin,
ranking de calificaciones) en lugar de duplicar sus consultas.
"""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.calificacion import Calificacion
from app.models.historia_hito import HistoriaHito
from app.models.localidad_kennedy import LocalidadKennedy
from app.modules.registry import MODULES
from app.modules.spec import ModuleSpec
from app.providers.tools import Locality, Milestone, ModuleSummary, NearPlace, RankedPlace
from app.repositories.geo_insights_repository import SqlGeoInsightsRepository
from app.repositories.rating_repository import SqlRatingRepository

SPECS = {spec.slug: spec for spec in MODULES}
# Módulos que no tienen sentido en «¿qué queda cerca?»: toda Kennedy, lotes, tramos y reportes.
NOT_NEARBY = {"localidad", "datos-catastrales", "estado-calles", "robos", "camaras-seguridad"}
RADIUS_M = 1500


class SqlBarrioTools:
    def __init__(self, session: Session, center: tuple[float, float]) -> None:
        self._session = session
        self._center = center

    def _label(self, spec: ModuleSpec, objeto_id: int) -> str | None:
        column: Any = getattr(spec.model, spec.label_field)
        value = self._session.scalar(select(column).where(spec.model.id == objeto_id))  # type: ignore[attr-defined]
        return None if value is None else str(value)

    def summary(self, slug: str) -> ModuleSummary:
        spec = SPECS[slug]
        total, verified, _ = SqlGeoInsightsRepository(self._session, spec.model).counts()
        model: Any = spec.model
        names = self._session.scalars(select(getattr(model, spec.label_field))
                                      .order_by(model.verified.desc(), model.id).limit(12))
        unique = dict.fromkeys(str(n) for n in names if n is not None)  # sin repetidos (p. ej. modalidades)
        return ModuleSummary(slug, total, verified, tuple(unique)[:3])

    def place_names(self, slug: str) -> list[tuple[str, str]]:
        """(nombre, estado) con estado = verificado | por_verificar | ejemplo (semilla inventada)."""
        spec = SPECS[slug]
        model: Any = spec.model
        rows = self._session.execute(select(getattr(model, spec.label_field), model.verified, model.source_type)
                                     .order_by(model.id))
        return [(str(n), "ejemplo" if s == "seed" else "verificado" if v else "por_verificar")
                for n, v, s in rows if n is not None]

    def totals(self) -> dict[str, int]:
        return {slug: SqlGeoInsightsRepository(self._session, spec.model).counts()[0]
                for slug, spec in SPECS.items()}

    def ratings_count(self) -> int:
        return self._session.scalar(select(func.count()).select_from(Calificacion)) or 0

    def best(self, slug: str | None) -> RankedPlace | None:
        for row in SqlRatingRepository(self._session).ranking(slug, 10):
            spec = SPECS.get(row.categoria_slug)
            name = self._label(spec, row.objeto_id) if spec else None
            if name is not None:
                return RankedPlace(row.categoria_slug, row.objeto_id, name, round(float(row.promedio), 2),
                                   row.total)
        return None

    def nearest(self, lon: float, lat: float, slug: str | None, limit: int = 3) -> list[NearPlace]:
        slugs = [slug] if slug else [s for s in SPECS if s not in NOT_NEARBY]
        found: list[NearPlace] = []
        for current in slugs:
            spec = SPECS[current]
            for objeto_id, meters in SqlGeoInsightsRepository(self._session, spec.model).nearby(
                    lon, lat, RADIUS_M, limit):
                name = self._label(spec, objeto_id)
                if name is not None:
                    found.append(NearPlace(current, objeto_id, name, meters))
        return sorted(found, key=lambda p: (p.distancia_m, p.slug, p.objeto_id))[:limit]

    def milestones(self) -> list[Milestone]:
        rows = self._session.scalars(select(HistoriaHito).order_by(HistoriaHito.anio, HistoriaHito.orden))
        return [Milestone(h.anio, h.titulo, h.verified) for h in rows]

    def locality(self) -> Locality | None:
        row = self._session.scalars(select(LocalidadKennedy).limit(1)).first()
        if row is None:
            return None
        area = float(row.superficie_km2) if row.superficie_km2 is not None else None
        return Locality(row.nombre_localidad, row.poblacion, area)

    def center(self) -> tuple[float, float]:
        return self._center
