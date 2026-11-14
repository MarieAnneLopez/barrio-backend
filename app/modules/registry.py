"""Registro de módulos CRUD expuestos en /api/v1.

Agregar un módulo = importar su SPEC y sumarlo aquí (H16 registra los demás).
"""

from app.modules import centros_educativos
from app.modules.spec import ModuleSpec

MODULES: tuple[ModuleSpec, ...] = (centros_educativos.SPEC,)
