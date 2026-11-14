"""Preguntas frecuentes bilingües (ES por defecto, EN)."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class FaqItem(Base):
    __tablename__ = "faq_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pregunta_es: Mapped[str] = mapped_column(Text)
    respuesta_es: Mapped[str] = mapped_column(Text)
    pregunta_en: Mapped[str] = mapped_column(Text)
    respuesta_en: Mapped[str] = mapped_column(Text)
    orden: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
