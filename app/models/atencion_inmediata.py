"""Módulo AtencionInmediata: tabla atencion_inmediata, geometría POINT (SRID 4326)."""

from typing import Any

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import AuditMixin, audit_checks, check_in, geom_column


class AtencionInmediata(AuditMixin, Base):
    __tablename__ = "atencion_inmediata"
    __table_args__ = audit_checks(check_in("tipo", ("cai", "hospital", "urgencias")))

    nombre: Mapped[str] = mapped_column(String(200))
    tipo: Mapped[str] = mapped_column(String(20))
    direccion: Mapped[str | None] = mapped_column(String(200))
    telefono_24_7: Mapped[str | None] = mapped_column(String(30))
    geom: Mapped[Any] = geom_column("POINT")
