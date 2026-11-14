"""Hitos de la historia de El Tintal y Kennedy; verified=False se muestra "por verificar"."""

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import AuditMixin, audit_checks


class HistoriaHito(AuditMixin, Base):
    __tablename__ = "historia_hitos"
    __table_args__ = audit_checks()

    anio: Mapped[int] = mapped_column(Integer)
    titulo: Mapped[str] = mapped_column(String(200))
    descripcion: Mapped[str] = mapped_column(Text)
    orden: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
