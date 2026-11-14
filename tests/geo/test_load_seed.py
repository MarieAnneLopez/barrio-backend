"""Carga de semillas de módulos: idempotente, validada y restringida a El Tintal."""

import json
import shutil
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CentroEducativo
from app.modules.centros_educativos import SPEC
from app.modules.registry import MODULES
from etl.load_seed import SEED, load_module


def _count(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(CentroEducativo)) or 0


def test_carga_real_es_idempotente(db_session: Session) -> None:
    first = load_module(db_session, SPEC)
    second = load_module(db_session, SPEC)

    assert first["loaded"] == second["loaded"] >= 1
    assert first["rejected"] == []
    assert _count(db_session) == first["loaded"]


def test_rechaza_fuera_del_poligono_y_datos_invalidos(db_session: Session, tmp_path: Path) -> None:
    shutil.copy(SEED / "el_tintal_polygon.geojson", tmp_path)
    (tmp_path / "modules").mkdir()
    base = {"tipo": "colegio", "caracter": "publico", "source_type": "osm"}
    features = [
        {"properties": {**base, "nombre": "Dentro", "source_ref": "a"},
         "geometry": {"type": "Point", "coordinates": [-74.1547809, 4.6430253]}},
        {"properties": {**base, "nombre": "En Fontibón", "source_ref": "b"},
         "geometry": {"type": "Point", "coordinates": [-74.1438049, 4.6649125]}},
        {"properties": {**base, "nombre": "Tipo raro", "tipo": "hospital", "source_ref": "c"},
         "geometry": {"type": "Point", "coordinates": [-74.1547809, 4.6430253]}},
    ]
    (tmp_path / "modules" / "centros-educativos.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}), encoding="utf-8"
    )

    result = load_module(db_session, SPEC, tmp_path)

    assert result["loaded"] == 1
    assert {r["source_ref"]: r["reason"] for r in result["rejected"]}["b"] == "fuera de El Tintal"
    assert "c" in {r["source_ref"] for r in result["rejected"]}


def test_todas_las_semillas_registradas_cargan_sin_rechazos(db_session: Session) -> None:
    for spec in MODULES:
        result = load_module(db_session, spec)
        assert result["loaded"] >= 1 and result["rejected"] == [], spec.slug
