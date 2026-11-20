"""Paginación y conteo públicos a partir de un único snapshot de PostgreSQL."""

from sqlalchemy import and_, cast, func, literal, select, String, true, union_all
from sqlalchemy.orm import Session

from app.models import Foto
from app.modules.registry import MODULES
from app.models.mixins import published


class SqlGalleryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def page(self, offset: int, limit: int) -> tuple[list[tuple[Foto, str]], int]:
        places = union_all(*(
            select(literal(spec.slug).label("slug"), spec.model.id.label("lugar_id"),
                   cast(getattr(spec.model, spec.label_field), String).label("nombre"))
            .where(published(spec.model))
            for spec in MODULES
        )).subquery()
        order = (Foto.categoria_slug, Foto.objeto_id, Foto.orden, Foto.id)
        visible = (select(Foto.id, places.c.nombre, *order[:-1])
                   .join(places, and_(places.c.slug == Foto.categoria_slug,
                                     places.c.lugar_id == Foto.objeto_id))).cte()
        count = select(func.count().label("total")).select_from(visible).subquery()
        ordered = (visible.c.categoria_slug, visible.c.objeto_id, visible.c.orden, visible.c.id)
        window = select(visible).order_by(*ordered).offset(offset).limit(limit).subquery()
        stmt = (select(Foto, window.c.nombre, count.c.total).select_from(count)
                .outerjoin(window, true()).outerjoin(Foto, Foto.id == window.c.id)
                .order_by(*order))
        rows = self._session.execute(stmt).all()
        return [(photo, name) for photo, name, _ in rows if photo is not None], rows[0][2]
