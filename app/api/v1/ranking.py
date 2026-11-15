"""Ranking global: los lugares mejor calificados de los 14 módulos (§11.3 punto 5)."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import SessionDep
from app.api.v1.place_labels import place_labeler
from app.repositories.rating_repository import SqlRatingRepository
from app.schemas.engagement import RankingItem
from app.services.ranking_service import GlobalRankingService

router = APIRouter(tags=["ranking"])


def get_ranking_service(session: SessionDep) -> GlobalRankingService:
    return GlobalRankingService(SqlRatingRepository(session), place_labeler(session))


@router.get("/ranking", response_model=list[RankingItem])
def global_ranking(service: Annotated[GlobalRankingService, Depends(get_ranking_service)],
                   limit: Annotated[int, Query(ge=1, le=50)] = 10) -> Any:
    return service.top(limit)
