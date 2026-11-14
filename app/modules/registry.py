"""Registro de módulos CRUD expuestos en /api/v1, en el orden del frontend (categoryConfig.ts).

Agregar un módulo = importar su SPEC y sumarlo aquí; el núcleo no cambia (OCP).
H17 registra los de polígono, línea y ficha.
"""

from app.modules import (
    atencion_inmediata, barberias, camaras_seguridad, centros_educativos, estaciones_transporte,
    librerias, robos, sitios_comida, veterinarias,
)
from app.modules.spec import ModuleSpec

MODULES: tuple[ModuleSpec, ...] = (
    centros_educativos.SPEC,
    camaras_seguridad.SPEC,
    estaciones_transporte.SPEC,
    sitios_comida.SPEC,
    librerias.SPEC,
    robos.SPEC,
    atencion_inmediata.SPEC,
    veterinarias.SPEC,
    barberias.SPEC,
)
