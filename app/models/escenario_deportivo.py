"""Módulo EscenarioDeportivo: tabla escenarios_deportivos, geometría POLYGON (SRID 4326)."""

from typing import Any

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import AuditMixin, audit_checks, check_in, geom_column


class EscenarioDeportivo(AuditMixin, Base):
    __tablename__ = "escenarios_deportivos"
    __table_args__ = audit_checks(check_in("acceso", ("libre", "restringido", "pago")))

    nombre: Mapped[str] = mapped_column(String(200))
    deportes: Mapped[str] = mapped_column(Text)
    superficie: Mapped[str | None] = mapped_column(String(60))
    iluminacion: Mapped[bool | None] = mapped_column(Boolean)
    horario: Mapped[str | None] = mapped_column(String(120))
    acceso: Mapped[str | None] = mapped_column(String(20))
    geom: Mapped[Any] = geom_column("POLYGON")
