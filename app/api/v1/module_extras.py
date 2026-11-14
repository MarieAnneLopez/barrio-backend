"""ModuleExtrasFactory: cercanía, ranking, estadísticas, calificaciones y galería de un módulo.

Se monta antes del router CRUD para que /cercania, /ranking y /stats no choquen
con /{item_id} (D10). Calificar exige sesión; subir o borrar fotos, admin.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import SessionDep
from app.api.guards import require_admin, require_user
from app.api.v1.router_factory import CrudRouterFactory
from app.modules.spec import ModuleSpec
from app.repositories.geo_insights_repository import SqlGeoInsightsRepository
from app.repositories.photo_repository import SqlPhotoRepository
from app.repositories.rating_repository import SqlRatingRepository
from app.schemas.engagement import (
    CalificacionIn, CalificacionOut, Cercano, Estadisticas, FotoIn, FotoOut, RankingItem,
    ResumenCalificaciones,
)
from app.services.crud_service import CrudService
from app.services.geo_insights_service import GeoInsightsService
from app.services.photo_service import PhotoService
from app.services.rating_service import RateableService

Lon = Annotated[float, Query(ge=-180, le=180)]
Lat = Annotated[float, Query(ge=-90, le=90)]
Limit = Annotated[int, Query(ge=1, le=50)]


class ModuleExtrasFactory:
    def __init__(self, spec: ModuleSpec) -> None:
        self.spec = spec
        self.crud = CrudRouterFactory(spec)

    def build(self) -> APIRouter:
        spec = self.spec
        router = APIRouter(prefix=f"/{spec.slug}", tags=[spec.slug])
        Items = Annotated[CrudService[Any], Depends(self.crud.service)]

        def ratings(session: SessionDep, items: Items) -> RateableService:
            return RateableService(spec.slug, spec.model, spec.label_field,
                                   SqlRatingRepository(session), items)

        def insights(session: SessionDep, items: Items) -> GeoInsightsService:
            return GeoInsightsService(spec.slug, SqlGeoInsightsRepository(session, spec.model),
                                      SqlRatingRepository(session), items)

        def photos(session: SessionDep, items: Items) -> PhotoService:
            return PhotoService(spec.slug, SqlPhotoRepository(session), items)

        Ratings = Annotated[RateableService, Depends(ratings)]
        Insights = Annotated[GeoInsightsService, Depends(insights)]
        Photos = Annotated[PhotoService, Depends(photos)]

        @router.get("/cercania", response_model=list[Cercano])
        def nearby(service: Insights, lon: Lon, lat: Lat, limit: Limit = 20,
                   radio_m: Annotated[float, Query(gt=0, le=5000)] = 500) -> Any:
            return service.nearby(lon, lat, radio_m, limit)

        @router.get("/ranking", response_model=list[RankingItem])
        def ranking(service: Ratings, limit: Limit = 10) -> Any:
            return service.ranking(limit)

        @router.get("/stats", response_model=Estadisticas)
        def stats(service: Insights) -> Any:
            return service.stats()

        @router.get("/{item_id}/calificaciones", response_model=ResumenCalificaciones)
        def list_ratings(item_id: int, service: Ratings, limit: Limit = 20) -> Any:
            return service.summary(item_id, limit)

        @router.post("/{item_id}/calificaciones", response_model=CalificacionOut,
                     status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_user)])
        def rate(item_id: int, payload: CalificacionIn, service: Ratings) -> Any:
            return service.rate(item_id, payload)

        @router.get("/{item_id}/fotos", response_model=list[FotoOut])
        def list_photos(item_id: int, service: Photos) -> Any:
            return service.list(item_id)

        @router.post("/{item_id}/fotos", response_model=FotoOut,
                     status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
        def add_photo(item_id: int, payload: FotoIn, service: Photos) -> Any:
            return service.add(item_id, payload)

        @router.delete("/{item_id}/fotos/{foto_id}", status_code=status.HTTP_204_NO_CONTENT,
                       dependencies=[Depends(require_admin)])
        def remove_photo(item_id: int, foto_id: int, service: Photos) -> Response:
            service.remove(item_id, foto_id)
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        return router
