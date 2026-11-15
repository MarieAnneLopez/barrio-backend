"""Módulo SitioComida: tabla sitios_comida, geometría POINT (SRID 4326)."""

from decimal import Decimal
from typing import Any

from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import AuditMixin, PublicationMixin, audit_checks, check_in, geom_column


class SitioComida(AuditMixin, PublicationMixin, Base):
    __tablename__ = "sitios_comida"
    __table_args__ = audit_checks(
        check_in("rango_precios", ("$", "$$", "$$$")),
        CheckConstraint("calificacion_promedio BETWEEN 0 AND 5", name="calificacion_promedio"),
    )

    nombre: Mapped[str] = mapped_column(String(200))
    especialidad: Mapped[str | None] = mapped_column(String(120))
    direccion: Mapped[str | None] = mapped_column(String(200))
    horario: Mapped[str | None] = mapped_column(String(120))
    rango_precios: Mapped[str | None] = mapped_column(String(5))
    calificacion_promedio: Mapped[Decimal | None] = mapped_column(Numeric(2, 1))
    geom: Mapped[Any] = geom_column("POINT")
