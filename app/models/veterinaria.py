"""Módulo Veterinaria: tabla veterinarias, geometría POINT (SRID 4326)."""

from decimal import Decimal
from typing import Any

from sqlalchemy import CheckConstraint, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import AuditMixin, PublicationMixin, audit_checks, geom_column


class Veterinaria(AuditMixin, PublicationMixin, Base):
    __tablename__ = "veterinarias"
    __table_args__ = audit_checks(
        CheckConstraint("calificacion_promedio BETWEEN 0 AND 5", name="calificacion_promedio"),
    )

    nombre: Mapped[str] = mapped_column(String(200))
    servicios: Mapped[str | None] = mapped_column(Text)
    direccion: Mapped[str | None] = mapped_column(String(200))
    horario: Mapped[str | None] = mapped_column(String(120))
    calificacion_promedio: Mapped[Decimal | None] = mapped_column(Numeric(2, 1))
    geom: Mapped[Any] = geom_column("POINT")
