"""Módulo Robo: tabla robos, geometría POINT (SRID 4326)."""

from datetime import date
from typing import Any

from sqlalchemy import CheckConstraint, Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import AuditMixin, PublicationMixin, audit_checks, check_in, geom_column


class Robo(AuditMixin, PublicationMixin, Base):
    __tablename__ = "robos"
    __table_args__ = audit_checks(
        check_in("franja_horaria", ("madrugada", "manana", "tarde", "noche")),
        CheckConstraint("cantidad >= 0", name="cantidad"),
    )

    fecha: Mapped[date] = mapped_column(Date)
    # Nula si la fuente no la reporta (la Línea 123 agrega por mes, D51).
    franja_horaria: Mapped[str | None] = mapped_column(String(20))
    modalidad: Mapped[str] = mapped_column(String(60))
    fuente: Mapped[str] = mapped_column(String(200))
    # Hechos agregados que representa el registro (dato anonimizado, §11.3 #10).
    cantidad: Mapped[int | None] = mapped_column(Integer)
    geom: Mapped[Any] = geom_column("POINT")
