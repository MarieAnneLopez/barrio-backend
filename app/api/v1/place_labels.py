"""Nombre de un lugar a partir de (categoria_slug, objeto_id), para ranking y galería."""

from sqlalchemy.orm import Session

from app.api.v1.router_factory import CrudRouterFactory
from app.core.exceptions import AppError
from app.modules.registry import MODULES
from app.services.ranking_service import Labeler

SPECS = {spec.slug: spec for spec in MODULES}


def place_labeler(session: Session) -> Labeler:
    def label(slug: str, objeto_id: int) -> str | None:
        spec = SPECS.get(slug)
        if spec is None:
            return None
        try:
            item = CrudRouterFactory(spec).service(session).get(objeto_id)
        except AppError:
            return None
        return str(getattr(item, spec.label_field))

    return label
