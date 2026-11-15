"""Contrato de las semillas reales: columnas del modelo, valores permitidos y trazabilidad.

Protege el paso de H15 (ETL) a H16/H17 (registro de los módulos): cada semilla
debe poder cargarse en su tabla tal como está.
"""

import json

import pytest
from sqlalchemy import CheckConstraint

import app.models as m
from etl.load_seed import SEED

TABLES = {
    "centros-educativos": m.CentroEducativo, "escenarios-deportivos": m.EscenarioDeportivo,
    "camaras-seguridad": m.CamaraSeguridad, "zonas-verdes": m.ZonaVerde,
    "datos-catastrales": m.DatoCatastral, "estado-calles": m.EstadoCalle,
    "estaciones-transporte": m.EstacionTransporte, "sitios-comida": m.SitioComida,
    "librerias": m.Libreria, "robos": m.Robo, "localidad": m.LocalidadKennedy,
    "atencion-inmediata": m.AtencionInmediata, "veterinarias": m.Veterinaria, "barberias": m.Barberia,
}
GEOMETRY = {"POINT": "Point", "POLYGON": "Polygon", "LINESTRING": "LineString",
            "MULTIPOLYGON": "MultiPolygon"}


def _allowed(model: type) -> dict[str, set[str]]:
    """Valores de los CHECK column IN (...) del modelo."""
    out = {}
    for c in model.__table__.constraints:
        text = str(getattr(c, "sqltext", ""))
        if isinstance(c, CheckConstraint) and " IN (" in text:
            column, values = text.split(" IN (")
            out[column] = {v.strip(" ')") for v in values.split(",")}
    return out


@pytest.mark.parametrize("slug", sorted(TABLES))
def test_semilla_cumple_el_modelo(slug: str) -> None:
    model = TABLES[slug]
    data = json.loads((SEED / "modules" / f"{slug}.geojson").read_text(encoding="utf-8"))
    columns = {c.name for c in model.__table__.columns} - {"id", "geom", "created_at", "updated_at"}
    # Obligatorias = sin NULL y sin valor por defecto del servidor (publicado = true, H35).
    required = ({c.name for c in model.__table__.columns if not c.nullable and c.server_default is None}
                & columns - {"source_type", "verified"})
    allowed, geom = _allowed(model), GEOMETRY[model.__table__.c.geom.type.geometry_type]

    assert data["features"], f"{slug} sin registros"
    for f in data["features"]:
        props = {k: v for k, v in f["properties"].items() if k != "osm_id"}
        assert set(props) <= columns, set(props) - columns
        assert all(props.get(k) is not None for k in required), (slug, props)
        assert all(props.get(k) is None or props[k] in v for k, v in allowed.items()), props
        assert f["geometry"]["type"] == geom and props["source_ref"]
        assert props["source_type"] != "seed" or (props["source_ref"] == "dato de ejemplo"
                                                   and props["verified"] is False)
