"""CrudRouterFactory: genera el router REST de un módulo a partir de su ModuleSpec.

Rutas estáticas (/geojson aquí; /cercania, /ranking y /stats en module_extras.py,
que se monta antes) preceden a /{item_id} (D10). Las escrituras dependen de require_admin.
"""

from functools import partial
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, Response, status

from app.api.deps import SessionDep
from app.api.guards import require_admin
from app.modules.spec import ModuleSpec
from app.repositories.base_geo_repo import BaseCrudRepository
from app.repositories.photo_repository import SqlPhotoRepository
from app.repositories.rating_repository import SqlRatingRepository
from app.repositories.query import MAX_PAGE_SIZE, ListQuery
from app.schemas.crud import FeatureCollectionOut, PageOut
from app.services.crud_service import CrudService

RESERVED = {"page", "size", "q", "sort"}


class CrudRouterFactory:
    def __init__(self, spec: ModuleSpec) -> None:
        self.spec = spec

    def service(self, session: SessionDep) -> CrudService[Any]:
        spec = self.spec
        repository = BaseCrudRepository(
            session, spec.model, spec.search_fields, spec.filter_fields, spec.sort_fields
        )
        cleanups = [partial(r.forget, spec.slug)
                    for r in (SqlRatingRepository(session), SqlPhotoRepository(session))]
        return CrudService(spec.slug, repository, spec.out_schema, cleanups)

    def build(self) -> APIRouter:
        spec = self.spec
        router = APIRouter(prefix=f"/{spec.slug}", tags=[spec.slug])
        Service = Annotated[CrudService[Any], Depends(self.service)]
        Out, Create, Update = spec.out_schema, spec.create_schema, spec.update_schema
        admin = [Depends(require_admin)]

        def list_query(
            request: Request,
            page: Annotated[int, Query(ge=1)] = 1,
            size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = 20,
            q: Annotated[str | None, Query(max_length=100)] = None,
            sort: Annotated[str | None, Query(max_length=40)] = None,
        ) -> ListQuery:
            filters = {k: v for k, v in request.query_params.items() if k not in RESERVED}
            return ListQuery(page=page, size=size, q=q, sort=sort, filters=filters)

        Params = Annotated[ListQuery, Depends(list_query)]

        @router.get("", response_model=PageOut[Out])  # type: ignore[valid-type]
        def list_items(service: Service, query: Params) -> Any:
            return service.list(query)

        @router.get("/geojson", response_model=FeatureCollectionOut)
        def geojson(service: Service, query: Params) -> Any:
            return service.feature_collection(query)

        @router.get("/{item_id}", response_model=Out)
        def get_item(item_id: int, service: Service) -> Any:
            return service.get(item_id)

        @router.post("", response_model=Out, status_code=status.HTTP_201_CREATED, dependencies=admin)
        def create_item(payload: Create, service: Service) -> Any:  # type: ignore[valid-type]
            return service.create(payload)

        @router.patch("/{item_id}", response_model=Out, dependencies=admin)
        def update_item(item_id: int, payload: Update, service: Service) -> Any:  # type: ignore[valid-type]
            return service.update(item_id, payload)

        @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=admin)
        def delete_item(item_id: int, service: Service) -> Response:
            service.delete(item_id)
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        return router
