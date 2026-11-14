"""Datos de ejemplo para los módulos sin ninguna fuente abierta con registros en El Tintal.

Se agregan solo si la semilla real tiene menos de MINIMO registros, con
source_type="seed", source_ref="dato de ejemplo" y verified=false: la UI los
rotula "dato de ejemplo". Nombres y códigos dicen "ejemplo"; las posiciones son
puntos pseudoaleatorios reproducibles (semilla fija) dentro de El Tintal.
Atención inmediata nunca recibe ejemplos: un CAI u hospital inventado podría
confundir a alguien en una emergencia.
"""

import json
from pathlib import Path
from typing import Any

from sqlalchemy import Connection, text

from app.core.database import get_engine
from etl.postgis_ops import load_clip_area
from etl.seed_writer import write_geojson

SEED = Path(__file__).resolve().parent.parent / "seed"
MINIMO = 3
POINTS_SQL = text("SELECT ST_X(p.geom), ST_Y(p.geom) FROM tintal_area a, "
                  "ST_Dump(ST_GeneratePoints(ST_Buffer(a.g, -0.002), :n, :seed)) p ORDER BY p.path")
TRACE = {"source_type": "seed", "source_ref": "dato de ejemplo", "verified": False}
TEMPLATES: dict[str, Any] = {
    "camaras-seguridad": lambda i: {
        "codigo": f"EJEMPLO-CAM-{i:02d}", "tipo": ("comunitaria", "policial", "privada")[i % 3],
        "operador": "Operador de ejemplo", "estado": "activa", "fecha_instalacion": None},
    "veterinarias": lambda i: {
        "nombre": f"Veterinaria de ejemplo {i}", "servicios": "Consulta general, vacunación",
        "direccion": None, "horario": "Mo-Sa 08:00-18:00"},
    "librerias": lambda i: {
        "nombre": f"Librería de ejemplo {i}", "direccion": None, "horario": "Mo-Sa 09:00-19:00",
        "especialidad": "Papelería y textos escolares"},
    "barberias": lambda i: {
        "nombre": f"Barbería de ejemplo {i}", "direccion": None, "horario": "Mo-Su 09:00-20:00",
        "servicios": "Corte, barba"},
}


def _collection(path: Path, slug: str) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"type": "FeatureCollection", "name": slug, "skipped": [], "features": []}


def complete(conn: Connection, slug: str, seed_dir: Path = SEED) -> int:
    """Agrega los ejemplos que falten hasta MINIMO; devuelve cuántos agregó."""
    path = seed_dir / "modules" / f"{slug}.geojson"
    data = _collection(path, slug)
    data["features"] = [f for f in data["features"]
                        if f["properties"].get("source_ref") != TRACE["source_ref"]]
    missing = MINIMO - len(data["features"])
    if missing > 0:
        seed = sum(map(ord, slug)) % 1000
        points = conn.execute(POINTS_SQL, {"n": missing, "seed": seed}).all()
        for i, (lon, lat) in enumerate(points, start=1):
            props = {**TEMPLATES[slug](i), **TRACE, "osm_id": f"ejemplo/{i:02d}"}
            data["features"].append({"type": "Feature", "properties": props, "geometry": {
                "type": "Point", "coordinates": [round(lon, 7), round(lat, 7)]}})
    write_geojson(path, data, pretty=True)
    return max(missing, 0)


def run(conn: Connection, seed_dir: Path = SEED) -> dict[str, int]:
    polygon = json.loads((seed_dir / "el_tintal_polygon.geojson").read_text(encoding="utf-8"))
    load_clip_area(conn, polygon["geometry"])
    return {slug: complete(conn, slug, seed_dir) for slug in TEMPLATES}


if __name__ == "__main__":
    with get_engine().begin() as connection:
        print(run(connection))
