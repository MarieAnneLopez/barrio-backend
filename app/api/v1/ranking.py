"""Ranking global: los lugares mejor calificados de los 14 módulos (§11.3 punto 5)."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import SessionDep
from app.api.v1.router_factory import CrudRouterFactory
from app.core.exceptions import AppError
from app.modules.registry import MODULES
from app.repositories.rating_repository import SqlRatingRepository
from app.schemas.engagement import RankingItem
from app.services.ranking_service import GlobalRankingService

router = APIRouter(tags=["ranking"])
SPECS = {spec.slug: spec for spec in MODULES}


def get_ranking_service(session: SessionDep) -> GlobalRankingService:
    def label(slug: str, objeto_id: int) -> str | None:
        spec = SPECS.get(slug)
        if spec is None:
            return None
        try:
            item = CrudRouterFactory(spec).service(session).get(objeto_id)
        except AppError:
            return None
        return str(getattr(item, spec.label_field))

    return GlobalRankingService(SqlRatingRepository(session), label)


@router.get("/ranking", response_model=list[RankingItem])
def global_ranking(service: Annotated[GlobalRankingService, Depends(get_ranking_service)],
                   limit: Annotated[int, Query(ge=1, le=50)] = 10) -> Any:
    return service.top(limit)
