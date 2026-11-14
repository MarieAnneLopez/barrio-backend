"""Registro de los 14 módulos CRUD expuestos en /api/v1, en el orden del frontend.

Agregar un módulo = importar su SPEC y sumarlo aquí; el núcleo no cambia (OCP).
"""

from app.modules import (
    atencion_inmediata, barberias, camaras_seguridad, centros_educativos, datos_catastrales,
    escenarios_deportivos, estaciones_transporte, estado_calles, librerias, localidad, robos,
    sitios_comida, veterinarias, zonas_verdes,
)
from app.modules.spec import ModuleSpec

MODULES: tuple[ModuleSpec, ...] = tuple(m.SPEC for m in (
    centros_educativos, escenarios_deportivos, camaras_seguridad, zonas_verdes, datos_catastrales,
    estado_calles, estaciones_transporte, sitios_comida, librerias, robos, localidad,
    atencion_inmediata, veterinarias, barberias,
))
