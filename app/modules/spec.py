"""ModuleSpec: todo lo que la fábrica CRUD necesita saber de un módulo.

Agregar el módulo #15 = un ModuleSpec nuevo en el registro; el núcleo
(repositorio, servicio, fábrica de routers) no se edita (Open/Closed).
"""

from dataclasses import dataclass
from functools import cached_property

from pydantic import BaseModel

from app.models.base import Base
from app.schemas.crud import output_schema, partial_schema


@dataclass(frozen=True)
class ModuleSpec:
    slug: str
    model: type[Base]
    create_schema: type[BaseModel]
    search_fields: tuple[str, ...] = ("nombre",)
    filter_fields: tuple[str, ...] = ("verified",)
    sort_fields: tuple[str, ...] = ("id", "nombre")

    @cached_property
    def update_schema(self) -> type[BaseModel]:
        return partial_schema(self.create_schema)

    @cached_property
    def out_schema(self) -> type[BaseModel]:
        return output_schema(self.create_schema)
