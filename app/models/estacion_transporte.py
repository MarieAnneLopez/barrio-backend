"""Módulo EstacionTransporte: tabla estaciones_transporte, geometría POINT (SRID 4326)."""

from typing import Any

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import AuditMixin, audit_checks, check_in, geom_column


class EstacionTransporte(AuditMixin, Base):
    __tablename__ = "estaciones_transporte"
    __table_args__ = audit_checks(check_in("tipo", ("troncal", "alimentador", "sitp")))

    nombre: Mapped[str] = mapped_column(String(200))
    tipo: Mapped[str] = mapped_column(String(20))
    lineas: Mapped[str | None] = mapped_column(Text)
    direccion: Mapped[str | None] = mapped_column(String(200))
    geom: Mapped[Any] = geom_column("POINT")
