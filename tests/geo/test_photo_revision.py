"""Las revisiones de fotos conservan bajas editoriales y aceptan altas nuevas."""

import json
from pathlib import Path
import shutil

import pytest

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import CentroEducativo, Foto
from etl import bootstrap, load_historia


def test_adopta_foto_borrada_y_carga_foto_nueva(
    db_session: Session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    shutil.copy(load_historia.SEED, tmp_path)
    monkeypatch.setattr(bootstrap, "get_settings", lambda: Settings(seed_dir=tmp_path, admin_email=""))
    place_ref = "https://www.openstreetmap.org/node/1"
    place = CentroEducativo(nombre="Colegio", tipo="colegio", caracter="publico", source_type="osm",
                            source_ref=place_ref, geom="SRID=4326;POINT(-74.1547809 4.6430253)")
    db_session.add(place)
    db_session.flush()
    base = {"modulo": "centros-educativos", "lugar_ref": place_ref, "alt_text": "El colegio",
            "autor": "Ana", "licencia": "CC BY 4.0", "orden": 0}
    removed = {**base, "url": "/assets/photos/borrada.webp",
               "source_ref": "https://commons.wikimedia.org/wiki/File:Borrada.jpg"}
    new = {**base, "url": "/assets/photos/nueva.webp",
           "source_ref": "https://commons.wikimedia.org/wiki/File:Nueva.jpg"}
    path = tmp_path / "fotos.json"
    path.write_text(json.dumps({"fotos": [removed]}), encoding="utf-8")
    stored = Foto(categoria_slug="centros-educativos", objeto_id=place.id, url=removed["url"],
                  alt_text=removed["alt_text"], source_type="seed", source_ref=removed["source_ref"])
    db_session.add(stored)
    db_session.flush()
    db_session.delete(stored)
    db_session.commit()

    bootstrap.main()
    assert list(db_session.scalars(select(Foto.url))) == []

    path.write_text(json.dumps({"fotos": [removed, new]}), encoding="utf-8")
    bootstrap.main()
    assert list(db_session.scalars(select(Foto.url))) == [new["url"]]
