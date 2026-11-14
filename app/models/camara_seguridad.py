"""Módulo CamaraSeguridad: tabla camaras_seguridad, geometría POINT (SRID 4326)."""

from datetime import date
from typing import Any

from sqlalchemy import Date, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import AuditMixin, audit_checks, check_in, geom_column


class CamaraSeguridad(AuditMixin, Base):
    __tablename__ = "camaras_seguridad"
    __table_args__ = audit_checks(
        check_in("tipo", ("policial", "comunitaria", "privada")),
        check_in("estado", ("activa", "inactiva", "mantenimiento")),
        UniqueConstraint("codigo"),
    )

    codigo: Mapped[str] = mapped_column(String(40))
    tipo: Mapped[str] = mapped_column(String(20))
    operador: Mapped[str | None] = mapped_column(String(120))
    estado: Mapped[str | None] = mapped_column(String(20))
    fecha_instalacion: Mapped[date | None] = mapped_column(Date)
    geom: Mapped[Any] = geom_column("POINT")
