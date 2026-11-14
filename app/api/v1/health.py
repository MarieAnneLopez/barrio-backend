"""GET /api/v1/health: 200 si la base y PostGIS responden, 503 si no."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import get_health_service
from app.schemas.health import HealthReport
from app.services.health_service import HealthService

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthReport,
    responses={503: {"model": HealthReport, "description": "Base de datos no disponible"}},
)
def health(
    response: Response,
    service: Annotated[HealthService, Depends(get_health_service)],
) -> HealthReport:
    report = service.check()
    if report.status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return report
