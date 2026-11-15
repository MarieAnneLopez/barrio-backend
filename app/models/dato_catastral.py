"""Módulo DatoCatastral: tabla datos_catastrales, geometría POLYGON (SRID 4326)."""

from decimal import Decimal
from typing import Any

from sqlalchemy import CheckConstraint, Float, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import AuditMixin, audit_checks, geom_column


class DatoCatastral(AuditMixin, Base):
    __tablename__ = "datos_catastrales"
    __table_args__ = audit_checks(
        CheckConstraint("estrato BETWEEN 1 AND 6", name="estrato"),
        UniqueConstraint("codigo_lote"),
    )

    codigo_lote: Mapped[str] = mapped_column(String(40))
    direccion: Mapped[str | None] = mapped_column(String(200))
    area_lote_m2: Mapped[float | None] = mapped_column(Float)
    area_construida_m2: Mapped[float | None] = mapped_column(Float)
    pisos: Mapped[int | None] = mapped_column(Integer)
    uso: Mapped[str | None] = mapped_column(String(40))
    avaluo_cop: Mapped[Decimal | None] = mapped_column(Numeric(16, 0))
    estrato: Mapped[int | None] = mapped_column(Integer)
    geom: Mapped[Any] = geom_column("POLYGON")
