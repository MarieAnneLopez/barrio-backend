"""Fotos de cada lugar: archivo local (nunca enlaces externos) con autor y licencia."""

from sqlalchemy import Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import AuditMixin, audit_checks


class Foto(AuditMixin, Base):
    __tablename__ = "fotos"
    __table_args__ = audit_checks(Index(None, "categoria_slug", "objeto_id"))

    categoria_slug: Mapped[str] = mapped_column(String(40))
    objeto_id: Mapped[int] = mapped_column(Integer)
    # Ruta bajo /assets/photos/ del frontend.
    url: Mapped[str] = mapped_column(String(500))
    alt_text: Mapped[str] = mapped_column(String(300))
    orden: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    autor: Mapped[str | None] = mapped_column(String(200))
    licencia: Mapped[str | None] = mapped_column(String(120))
