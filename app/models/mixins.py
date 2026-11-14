"""Columnas comunes: identificador, trazabilidad de la fuente y auditoría (§7.5)."""

from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, CheckConstraint, Constraint, DateTime, Index, Integer, String, Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import SRID

SOURCE_TYPES = ("osm", "datos_abiertos", "seed")


class AuditMixin:
    """id + source_type/source_ref/verified + created_at/updated_at."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_type: Mapped[str] = mapped_column(String(20), default="seed", server_default="seed")
    source_ref: Mapped[str | None] = mapped_column(Text)
    # Falso = "por verificar" en la UI; las semillas inventadas son "dato de ejemplo".
    verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


def check_in(column: str, values: tuple[str, ...]) -> CheckConstraint:
    """CHECK column IN (...): más fácil de migrar que un ENUM de PostgreSQL."""
    allowed = ", ".join(f"'{v}'" for v in values)
    return CheckConstraint(f"{column} IN ({allowed})", name=column)


def audit_checks(*extra: Constraint | Index) -> tuple[Constraint | Index, ...]:
    return (check_in("source_type", SOURCE_TYPES), *extra)


def geom_column(geometry_type: str, nullable: bool = False) -> Mapped[Any]:
    """Columna geom(<tipo>, 4326) con índice GIST (spatial_index=True de GeoAlchemy2)."""
    return mapped_column(
        Geometry(geometry_type=geometry_type, srid=SRID, spatial_index=True),
        nullable=nullable,
    )
