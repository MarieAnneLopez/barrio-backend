"""Módulo Robo: tabla robos, geometría POINT (SRID 4326)."""

from datetime import date
from typing import Any

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import AuditMixin, audit_checks, check_in, geom_column


class Robo(AuditMixin, Base):
    __tablename__ = "robos"
    __table_args__ = audit_checks(
        check_in("franja_horaria", ("madrugada", "manana", "tarde", "noche")),
    )

    fecha: Mapped[date] = mapped_column(Date)
    franja_horaria: Mapped[str] = mapped_column(String(20))
    modalidad: Mapped[str] = mapped_column(String(60))
    fuente: Mapped[str] = mapped_column(String(200))
    geom: Mapped[Any] = geom_column("POINT")
