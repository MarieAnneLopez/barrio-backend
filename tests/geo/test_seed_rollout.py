"""Un despliegue reanudado conserva el estado editorial y las relaciones."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import shutil

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import get_engine
from app.models import Calificacion, CentroEducativo, Foto
from etl import bootstrap, load_fotos, load_historia, load_seed
from tests.api.crud_app import POINT


@pytest.fixture
def bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "modules").mkdir()
    shutil.copy(load_seed.SEED / "el_tintal_polygon.geojson", tmp_path)
    shutil.copy(load_historia.SEED, tmp_path)
    (tmp_path / "fotos.json").write_text('{"fotos": []}', encoding="utf-8")
    monkeypatch.setattr(bootstrap, "get_settings", lambda: Settings(seed_dir=tmp_path, admin_email=""))
    return tmp_path


def schools(bundle: Path, *names: str) -> None:
    features = [
        {"geometry": POINT, "properties": {
            "tipo": "colegio", "caracter": "publico", "source_type": "osm",
            "nombre": name, "source_ref": ref(n), "descripcion_es": name,
        }} for n, name in enumerate(names, start=1)
    ]
    (bundle / "modules" / "centros-educativos.geojson").write_text(
        json.dumps({"features": features}), encoding="utf-8")


def ref(n: int) -> str:
    return f"https://www.openstreetmap.org/node/{n}"


def test_adopta_ediciones_y_bajas_en_primera_publicacion_y_agrega_solo_lugares_nuevos(
    db_session: Session, bundle: Path,
) -> None:
    schools(bundle, "Nombre de la semilla", "Retirado")
    row = CentroEducativo(nombre="Nombre editado", tipo="colegio", caracter="publico", source_type="osm",
                          source_ref=ref(1), publicado=False,
                          geom="SRID=4326;POINT(-74.1547809 4.6430253)")
    db_session.add(row)
    db_session.flush()
    db_session.add(Foto(categoria_slug="centros-educativos", objeto_id=row.id,
                        url="/assets/photos/editorial.webp", alt_text="Foto revisada"))
    db_session.add(Calificacion(categoria_slug="centros-educativos", objeto_id=row.id, estrellas=4))
    db_session.commit()
    school_id = row.id
    bootstrap.main()
    schools(bundle, "Otro nombre de la semilla", "Retirado", "Nuevo")
    bootstrap.main()
    db_session.expire_all()
    result = [(r.id, r.nombre, r.publicado) for r in db_session.scalars(
        select(CentroEducativo).order_by(CentroEducativo.id))]
    assert result == [(school_id, "Nombre editado", False), (school_id + 1, "Nuevo", True)]
    assert db_session.scalar(select(Foto.objeto_id)) == school_id
    assert db_session.scalar(select(Calificacion.objeto_id)) == school_id


def test_error_revierte_la_carga_y_dos_arranques_no_duplican(
    db_session: Session, bundle: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    schools(bundle, "Uno", "Dos")
    foto = {"modulo": "centros-educativos", "lugar_ref": ref(1), "url": "/assets/photos/uno.webp",
            "alt_text": "Foto de Uno", "autor": "Ana", "licencia": "CC BY 4.0", "orden": 0,
            "source_ref": "https://commons.wikimedia.org/wiki/File:Uno.jpg"}
    (bundle / "fotos.json").write_text(json.dumps({"fotos": [foto]}), encoding="utf-8")
    with monkeypatch.context() as patch:
        def fail(*args: object, **kwargs: object) -> None:
            raise RuntimeError("interrupción")

        patch.setattr(load_fotos, "read", fail)
        with pytest.raises(RuntimeError, match="interrupción"):
            bootstrap.main()
    assert db_session.scalar(select(CentroEducativo.id)) is None
    db_session.rollback()
    with ThreadPoolExecutor(max_workers=2) as workers:
        for future in (workers.submit(bootstrap.main), workers.submit(bootstrap.main)):
            future.result(timeout=40)
    with Session(get_engine()) as checked:
        assert len(list(checked.scalars(select(CentroEducativo.id)))) == 2
        assert len(list(checked.scalars(select(Foto.id)))) == 1
