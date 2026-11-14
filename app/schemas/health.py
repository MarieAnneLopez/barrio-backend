"""Contrato de /api/v1/health."""

from typing import Literal

from pydantic import BaseModel


class HealthReport(BaseModel):
    status: Literal["ok", "degraded"]
    database: Literal["ok", "unavailable"]
    postgis: str | None
