"""Orquestador de datos abiertos de extremo a extremo, sin red: fuentes locales + PostGIS real."""

import json
import zipfile
from pathlib import Path
from typing import Any

from sqlalchemy import Connection

from etl.datos_abiertos import sources as s
from etl.import_datos_abiertos import run
from etl.load_seed import SEED
from etl.tintal_config import UPZ_RELATIONS
from tests.geo.etl_fixtures import INSIDE, area_conn, square_wkb, write_gpkg  # noqa: F401

X, Y = INSIDE


def _ring(d: float) -> list[dict[str, float]]:
    pts = [(X - d, Y - d), (X + d, Y - d), (X + d, Y + d), (X - d, Y + d), (X - d, Y - d)]
    return [{"lon": a, "lat": b} for a, b in pts]


def _relation(rid: int, d: float) -> dict[str, Any]:
    return {"type": "relation", "id": rid, "members": [{"type": "way", "role": "outer", "geometry": _ring(d)}]}


class FakeOverpass:
    def query(self, ql: str) -> dict[str, Any]:
        if "4740229" in ql:
            return {"elements": [_relation(4740229, 0.05)]}
        return {"elements": [_relation(rid, 0.001) for rid in UPZ_RELATIONS]}


class FakeData:
    def __init__(self, files: dict[str, Path]) -> None:
        self.files = files

    def fetch(self, url: str) -> Path:
        return self.files[url]


def _point(props: dict[str, Any]) -> dict[str, Any]:
    return {"type": "Feature", "properties": props, "geometry": {"type": "Point", "coordinates": [X, Y]}}


def _files(conn: Connection, tmp: Path) -> dict[str, Path]:
    def w(name: str, content: str) -> Path:
        (tmp / name).write_text(content, encoding="utf-8")
        return tmp / name

    box = (X - 0.0002, Y - 0.0002, X + 0.0002, Y + 0.0002)
    write_gpkg(tmp / "LOTE.gpkg", "LOTE", "geom", "LOTCODIGO", [("1", square_wkb(conn, X, Y), box)])
    with zipfile.ZipFile(tmp / "lote.zip", "w") as z:
        z.write(tmp / "LOTE.gpkg", "LOTE.gpkg")
    with zipfile.ZipFile(tmp / "alc.zip", "w") as z:
        z.writestr("GeoJson/alcaldialocal.json", json.dumps({"features": [{"attributes": {
            "COD_LOC": "08", "NOM_ALCALDIA": "Alcaldía Local de Kennedy", "DIRECCION": "Calle 19 Sur"}}]}))
    cai = {"CAINOMBRE": "CAI Tintal", "CAIHORARIO": "24 horas", "CAITELEFON": "313", "CAIIDENTIF": "E1"}
    return {
        s.NUSE_123.url: w("n.csv", '"ID";"ANIO";"MES";"TIPO_DETALLE";"COD_UPZ";"CANT_INCIDENTES"\n'
                                   '"A";"2025";"02";"HURTO EFECTUADO";"UPZ79";7\n'),
        s.CAI.url: w("c.json", json.dumps({"features": [_point(cai)]})),
        s.IPS.url: w("i.json", json.dumps({"features": [_point({"nombre": "Hospital X", "codigo_pre": "9"})]})),
        s.LOTE.url: tmp / "lote.zip",
        s.ESTRATO.url: write_gpkg(tmp / "e.gpkg", "ManzanaEstratificacion", "Shape", "ESTRATO", []),
        s.POBLACION.url: w("p.csv", "ANO;CODIGO_LOCALIDAD;POBLACION\n2026;8;42\n"),
        s.ALCALDIA.url: tmp / "alc.zip",
    }


def test_run_escribe_las_cuatro_semillas(area_conn: Connection, tmp_path: Path) -> None:
    (tmp_path / "seed" / "modules").mkdir(parents=True)
    (tmp_path / "seed" / "el_tintal_polygon.geojson").write_bytes((SEED / "el_tintal_polygon.geojson").read_bytes())

    summary = run(area_conn, FakeOverpass(), FakeData(_files(area_conn, tmp_path)), tmp_path / "seed")  # type: ignore[arg-type]
    read = lambda slug: json.loads((tmp_path / "seed" / "modules" / f"{slug}.geojson").read_text("utf-8"))  # noqa: E731

    assert summary == {"robos": 1, "atencion-inmediata": 2, "datos-catastrales": 1, "localidad": 1}
    assert read("robos")["features"][0]["properties"]["cantidad"] == 7
    ficha = read("localidad")["features"][0]["properties"]
    assert ficha["poblacion"] == 42 and ficha["alcaldia_local"] == "Alcaldía Local de Kennedy, Calle 19 Sur"
    assert read("datos-catastrales")["features"][0]["properties"]["estrato"] is None
    assert "Secretaría Distrital de Salud, CC BY 4.0" in read("atencion-inmediata")["license"]
