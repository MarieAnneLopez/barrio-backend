"""Cargas mínimas válidas por módulo (campos obligatorios de §11.3) para las pruebas de API."""

from typing import Any

POINT = {"type": "Point", "coordinates": [-74.1547809, 4.6430253]}

PAYLOADS: dict[str, dict[str, Any]] = {
    "centros-educativos": {"nombre": "Colegio Alfa", "tipo": "colegio", "caracter": "publico"},
    "camaras-seguridad": {"codigo": "CAM-PRUEBA-1", "tipo": "comunitaria", "estado": "activa"},
    "estaciones-transporte": {"nombre": "Paradero Alfa", "tipo": "sitp", "lineas": "8-3"},
    "sitios-comida": {"nombre": "Asadero Alfa", "rango_precios": "$$"},
    "librerias": {"nombre": "Librería Alfa", "especialidad": "Libros"},
    "robos": {"fecha": "2025-02-01", "modalidad": "Hurto efectuado", "fuente": "Prueba", "cantidad": 3},
    "atencion-inmediata": {"nombre": "CAI Alfa", "tipo": "cai", "telefono_24_7": "601 123 4567"},
    "veterinarias": {"nombre": "Veterinaria Alfa", "servicios": "Consulta"},
    "barberias": {"nombre": "Barbería Alfa", "servicios": "Corte"},
}
# Un campo editable y su nuevo valor, por módulo.
PATCHES: dict[str, tuple[str, Any]] = {
    "centros-educativos": ("jornadas", "mañana"), "camaras-seguridad": ("estado", "mantenimiento"),
    "estaciones-transporte": ("tipo", "alimentador"), "sitios-comida": ("especialidad", "pollo"),
    "librerias": ("horario", "Mo-Fr 09:00-18:00"), "robos": ("franja_horaria", "noche"),
    "atencion-inmediata": ("tipo", "hospital"), "veterinarias": ("horario", "24/7"),
    "barberias": ("direccion", "Calle 6 # 87-10"),
}


def payload(slug: str, **extra: Any) -> dict[str, Any]:
    return {**PAYLOADS[slug], "geometry": POINT, **extra}
