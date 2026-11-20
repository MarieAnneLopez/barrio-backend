"""Última revisión aplicada de cada semilla y sus identidades editoriales."""
from typing import Any

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SeedManifest(Base):
    __tablename__ = "seed_manifests"

    scope: Mapped[str] = mapped_column(String(100), primary_key=True)
    digest: Mapped[str] = mapped_column(String(64))
    records: Mapped[dict[str, Any]] = mapped_column(JSONB)
