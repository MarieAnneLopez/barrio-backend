"""Módulo ZonaVerde: tabla zonas_verdes, geometría POLYGON (SRID 4326)."""

from typing import Any

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import AuditMixin, PublicationMixin, audit_checks, check_in, geom_column


class ZonaVerde(AuditMixin, PublicationMixin, Base):
    __tablename__ = "zonas_verdes"
    __table_args__ = audit_checks(
        check_in("tipo", ("parque", "alameda", "jardin")),
        check_in("arborizacion", ("alta", "media", "baja")),
        check_in("estado", ("bueno", "regular", "malo")),
    )

    nombre: Mapped[str] = mapped_column(String(200))
    area_m2: Mapped[float | None] = mapped_column(Float)
    tipo: Mapped[str] = mapped_column(String(20))
    arborizacion: Mapped[str | None] = mapped_column(String(20))
    estado: Mapped[str | None] = mapped_column(String(20))
    geom: Mapped[Any] = geom_column("POLYGON")
