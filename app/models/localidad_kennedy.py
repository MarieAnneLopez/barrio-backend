"""Módulo LocalidadKennedy: tabla localidad_kennedy, geometría MULTIPOLYGON (SRID 4326)."""

from typing import Any

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import AuditMixin, PublicationMixin, audit_checks, geom_column


class LocalidadKennedy(AuditMixin, PublicationMixin, Base):
    __tablename__ = "localidad_kennedy"
    __table_args__ = audit_checks()

    nombre_localidad: Mapped[str] = mapped_column(String(120))
    bandera_url: Mapped[str | None] = mapped_column(String(300))
    historia: Mapped[str | None] = mapped_column(Text)
    poblacion: Mapped[int | None] = mapped_column(Integer)
    superficie_km2: Mapped[float | None] = mapped_column(Float)
    alcaldia_local: Mapped[str | None] = mapped_column(String(200))
    retos: Mapped[str | None] = mapped_column(Text)
    geom: Mapped[Any] = geom_column("MULTIPOLYGON", nullable=True)
