"""Módulo EstadoCalle: tabla estado_calles, geometría LINESTRING (SRID 4326)."""

from datetime import date
from typing import Any

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import AuditMixin, audit_checks, check_in, geom_column


class EstadoCalle(AuditMixin, Base):
    __tablename__ = "estado_calles"
    __table_args__ = audit_checks(check_in("estado", ("bueno", "regular", "malo")))

    nombre_via: Mapped[str] = mapped_column(String(200))
    tipo_via: Mapped[str | None] = mapped_column(String(40))
    material: Mapped[str | None] = mapped_column(String(40))
    # Nulo = "por verificar": ninguna fuente abierta da la clase por tramo (D51).
    estado: Mapped[str | None] = mapped_column(String(20))
    ultima_intervencion: Mapped[date | None] = mapped_column(Date)
    reportes_ciudadanos: Mapped[int | None] = mapped_column(Integer)
    geom: Mapped[Any] = geom_column("LINESTRING")
