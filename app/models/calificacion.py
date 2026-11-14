"""Calificaciones polimórficas: categoria_slug + objeto_id, de 0.0 a 5.0 en pasos de 0.5."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Calificacion(Base):
    __tablename__ = "calificaciones"
    __table_args__ = (
        CheckConstraint(
            "estrellas BETWEEN 0 AND 5 AND estrellas * 2 = floor(estrellas * 2)",
            name="estrellas",
        ),
        Index(None, "categoria_slug", "objeto_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    categoria_slug: Mapped[str] = mapped_column(String(40))
    objeto_id: Mapped[int] = mapped_column(Integer)
    estrellas: Mapped[Decimal] = mapped_column(Numeric(2, 1))
    comentario: Mapped[str | None] = mapped_column(Text)
    autor_nombre: Mapped[str | None] = mapped_column(String(120))
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
