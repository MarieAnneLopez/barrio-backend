"""Usuarios con rol admin (CRUD completo) o visitante (consulta y calificaciones)."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import check_in

ROLES = ("admin", "visitante")


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (check_in("rol", ROLES), UniqueConstraint("email"))

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(254))
    nombre: Mapped[str] = mapped_column(String(120))
    # Solo el hash (bcrypt, H21); nunca la clave en texto plano.
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[str] = mapped_column(String(20), default="visitante", server_default="visitante")
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
