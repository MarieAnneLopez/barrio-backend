"""Módulo CentroEducativo: tabla centros_educativos, geometría POINT (SRID 4326)."""

from typing import Any

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import AuditMixin, PublicationMixin, audit_checks, check_in, geom_column


class CentroEducativo(AuditMixin, PublicationMixin, Base):
    __tablename__ = "centros_educativos"
    __table_args__ = audit_checks(
        check_in("tipo", ("jardin", "colegio", "universidad")),
        check_in("caracter", ("publico", "privado")),
    )

    nombre: Mapped[str] = mapped_column(String(200))
    tipo: Mapped[str] = mapped_column(String(20))
    caracter: Mapped[str] = mapped_column(String(10))
    direccion: Mapped[str | None] = mapped_column(String(200))
    jornadas: Mapped[str | None] = mapped_column(Text)
    niveles: Mapped[str | None] = mapped_column(Text)
    telefono: Mapped[str | None] = mapped_column(String(30))
    geom: Mapped[Any] = geom_column("POINT")
