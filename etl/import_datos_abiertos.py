"""ETL datos abiertos de Bogotá → semillas de robos, atención, catastro y localidad.

Uso (desde barrio-backend/, con PostGIS arriba): python -m etl.import_datos_abiertos
Descarga una vez cada archivo (caché en etl/.cache/), filtra a El Tintal en
PostGIS (D4) y reescribe seed/modules/<slug>.geojson. Idempotente.
"""

import json
import zipfile
from pathlib import Path
from typing import Any

from sqlalchemy import Connection

from app.core.database import get_engine
from etl.datos_abiertos import atencion, catastro, localidad, robos
from etl.datos_abiertos.client import OpenDataClient, read_text
from etl.datos_abiertos.geo import inside, point_on_surface
from etl.datos_abiertos.sources import ALCALDIA, CAI, ESTRATO, IPS, LOTE, NUSE_123, POBLACION, Source
from etl.osm_geometry import relation_outer_wkt
from etl.overpass import OverpassClient
from etl.postgis_ops import load_clip_area
from etl.seed_writer import write_geojson
from etl.tintal_config import OSM_LICENSE, UPZ_RELATIONS, polygon_query

SEED = Path(__file__).resolve().parent.parent / "seed"


def _write(seed_dir: Path, slug: str, features: list[dict[str, Any]], sources: list[Source],
           skipped: list[dict[str, Any]] | None = None, pretty: bool = True) -> int:
    collection = {"type": "FeatureCollection", "name": slug,
                  "license": "; ".join(sorted({f"{s.entity}, {s.license}" for s in sources})),
                  "sources": [s.page for s in sources], "skipped": skipped or [],
                  "features": features}
    write_geojson(seed_dir / "modules" / f"{slug}.geojson", collection, pretty=pretty)
    return len(features)


def _upz_points(osm: OverpassClient, conn: Connection) -> dict[str, list[float]]:
    relations = [e for e in osm.query(polygon_query())["elements"] if e["type"] == "relation"]
    code = {rid: f"UPZ{name.split()[1]}" for rid, name in UPZ_RELATIONS.items()}
    return {code[r["id"]]: point_on_surface(conn, relation_outer_wkt(r)) for r in relations}


def _gpkg(data: OpenDataClient, source: Source, member: str | None) -> Path:
    path = data.fetch(source.url)
    if member is None:
        return path
    target = path.with_name(path.name + "_" + member)
    if not target.exists():
        with zipfile.ZipFile(path) as z, z.open(member) as src, target.open("wb") as dst:
            while chunk := src.read(1 << 20):
                dst.write(chunk)
    return target


def run(conn: Connection, osm: OverpassClient, data: OpenDataClient, seed_dir: Path = SEED
        ) -> dict[str, int]:
    polygon = json.loads((seed_dir / "el_tintal_polygon.geojson").read_text(encoding="utf-8"))
    load_clip_area(conn, polygon["geometry"])
    summary: dict[str, int] = {}
    nuse = read_text(data.fetch(NUSE_123.url))
    summary["robos"] = _write(seed_dir, "robos", robos.features(nuse, _upz_points(osm, conn)),
                              [NUSE_123])
    cai = inside(conn, atencion.cai_features(json.loads(read_text(data.fetch(CAI.url)))))
    ips_all = json.loads(read_text(data.fetch(IPS.url)))
    ips_all["features"] = inside(conn, [f for f in ips_all["features"] if f.get("geometry")])
    hospitals, skipped = atencion.ips_features(ips_all)
    summary["atencion-inmediata"] = _write(seed_dir, "atencion-inmediata", cai + hospitals,
                                           [CAI, IPS], skipped)
    lots = catastro.features(conn, _gpkg(data, LOTE, "LOTE.gpkg"), _gpkg(data, ESTRATO, None))
    summary["datos-catastrales"] = _write(seed_dir, "datos-catastrales", lots, [LOTE, ESTRATO],
                                          pretty=False)
    kennedy = osm.query(f"[out:json][timeout:120];relation({localidad.KENNEDY_RELATION});out geom;")
    alcaldias = json.loads(zipfile.ZipFile(data.fetch(ALCALDIA.url)).read(
        "GeoJson/alcaldialocal.json").decode("utf-8-sig"))
    ficha = localidad.feature(conn, relation_outer_wkt(kennedy["elements"][0]),
                              read_text(data.fetch(POBLACION.url)), alcaldias)
    summary["localidad"] = _write(seed_dir, "localidad", [ficha], [POBLACION, ALCALDIA])
    return summary


if __name__ == "__main__":
    with get_engine().begin() as connection:
        print(run(connection, OverpassClient(), OpenDataClient()), OSM_LICENSE)
