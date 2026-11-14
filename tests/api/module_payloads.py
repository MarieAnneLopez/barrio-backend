"""Cargas mínimas válidas por módulo (campos obligatorios de §11.3) para las pruebas de API."""

from typing import Any

POINT = {"type": "Point", "coordinates": [-74.1547809, 4.6430253]}
_RING = [[-74.155, 4.643], [-74.154, 4.643], [-74.154, 4.644], [-74.155, 4.644], [-74.155, 4.643]]
POLYGON = {"type": "Polygon", "coordinates": [_RING]}
LINE = {"type": "LineString", "coordinates": [[-74.155, 4.643], [-74.154, 4.6435]]}
MULTI = {"type": "MultiPolygon", "coordinates": [[_RING]]}
GEOMETRY = {"escenarios-deportivos": POLYGON, "zonas-verdes": POLYGON, "datos-catastrales": POLYGON,
            "estado-calles": LINE, "localidad": MULTI}

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
    "escenarios-deportivos": {"nombre": "Cancha Alfa", "deportes": "fútbol", "iluminacion": True},
    "zonas-verdes": {"nombre": "Parque Alfa", "tipo": "parque", "area_m2": 1200.5},
    "datos-catastrales": {"matricula_inmobiliaria": "004601001001", "estrato": 2, "area_lote_m2": 48},
    "estado-calles": {"nombre_via": "Calle 6D", "material": "asfalto"},
    "localidad": {"nombre_localidad": "Kennedy", "poblacion": 1104934, "bandera_url": "/assets/kennedy/bandera.svg"},
}
# Un campo editable y su nuevo valor, por módulo.
PATCHES: dict[str, tuple[str, Any]] = {
    "centros-educativos": ("jornadas", "mañana"), "camaras-seguridad": ("estado", "mantenimiento"),
    "estaciones-transporte": ("tipo", "alimentador"), "sitios-comida": ("especialidad", "pollo"),
    "librerias": ("horario", "Mo-Fr 09:00-18:00"), "robos": ("franja_horaria", "noche"),
    "atencion-inmediata": ("tipo", "hospital"), "veterinarias": ("horario", "24/7"),
    "barberias": ("direccion", "Calle 6 # 87-10"),
    "escenarios-deportivos": ("acceso", "libre"), "zonas-verdes": ("arborizacion", "alta"),
    "datos-catastrales": ("pisos", 3), "estado-calles": ("estado", "regular"),
    "localidad": ("retos", "Movilidad y seguridad"),
}


def payload(slug: str, **extra: Any) -> dict[str, Any]:
    return {**PAYLOADS[slug], "geometry": GEOMETRY.get(slug, POINT), **extra}
