"""Esquemas genéricos del CRUD: entrada con auditoría, parcial (PATCH), salida y página."""

from datetime import datetime
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, create_model

T = TypeVar("T")
AUDIT_FIELDS = ("source_type", "source_ref", "verified")


class AuditIn(BaseModel):
    """Trazabilidad declarada al crear; extra="forbid" impide asignar id o fechas."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    source_type: Literal["osm", "datos_abiertos", "seed"] = "seed"
    source_ref: str | None = Field(None, max_length=500)
    verified: bool = False


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source_type: str
    source_ref: str | None
    verified: bool
    created_at: datetime
    updated_at: datetime


def partial_schema(create: type[BaseModel]) -> type[BaseModel]:
    """Todos los campos opcionales; enviar null a uno obligatorio sigue fallando (422)."""
    fields: dict[str, Any] = {
        name: (info.annotation, Field(None, **_constraints(info)))
        for name, info in create.model_fields.items()
    }
    return create_model(
        create.__name__.replace("Create", "Update"),
        __config__=ConfigDict(extra="forbid", str_strip_whitespace=True),
        **fields,
    )


def output_schema(create: type[BaseModel]) -> type[BaseModel]:
    fields: dict[str, Any] = {
        name: (info.annotation, ...)
        for name, info in create.model_fields.items()
        if name not in AUDIT_FIELDS and name != "geometry"
    }
    fields["geometry"] = (dict[str, Any] | None, None)
    return create_model(create.__name__.replace("Create", "Out"), __base__=AuditOut, **fields)


def _constraints(info: Any) -> dict[str, Any]:
    """Conserva longitudes y patrones del esquema de creación."""
    out: dict[str, Any] = {}
    for meta in info.metadata:
        for key in ("min_length", "max_length", "pattern", "ge", "le"):
            if getattr(meta, key, None) is not None:
                out[key] = getattr(meta, key)
    return out


class PageOut(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int


class FeatureCollectionOut(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[dict[str, Any]]
