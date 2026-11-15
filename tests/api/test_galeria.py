"""D66: fotos reales de Commons en la semilla y Galería General (/api/v1/fotos)."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_engine
from app.models import Foto
from etl import load_fotos
from tests.api.crud_app import crud_app
from tests.api.test_engagement import barberia
from tests.conftest import make_client

pytestmark = pytest.mark.usefixtures("db_session")
OSM = "https://www.openstreetmap.org/node/1"
PHOTO = {"modulo": "barberias", "lugar_ref": OSM, "url": "/assets/photos/lugares/alfa-1280.webp",
         "alt_text": "Fachada de la barbería Alfa", "orden": 0, "autor": "Ana", "licencia": "CC BY 4.0",
         "source_ref": "https://commons.wikimedia.org/wiki/File:Alfa.jpg"}


def seed(tmp_path: Path, *fotos: dict[str, object]) -> Path:
    path = tmp_path / "fotos.json"
    path.write_text(json.dumps({"fotos": list(fotos)}), encoding="utf-8")
    return path


def test_la_semilla_solo_trae_fotos_locales_de_commons_con_autor_y_licencia() -> None:
    fotos = load_fotos.read()
    assert len(fotos) == 7
    assert all(f["url"].startswith("/assets/photos/") and f["licencia"].startswith("CC BY") for f in fotos)
    assert {f["modulo"] for f in fotos} == {"estaciones-transporte"}


def test_rechaza_fotos_externas_o_sin_pagina_de_commons(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        load_fotos.read(seed(tmp_path, {**PHOTO, "url": "https://x.com/a.jpg"}))
    with pytest.raises(ValueError, match="Commons"):
        load_fotos.read(seed(tmp_path, {**PHOTO, "source_ref": "https://x.com/a"}))
    with pytest.raises(ValueError, match="módulo"):
        load_fotos.read(seed(tmp_path, {**PHOTO, "modulo": "nada"}))


async def test_carga_idempotente_y_galeria_general(tmp_path: Path, db_session: Session) -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        item = await barberia(http, "Alfa", source_type="osm", source_ref=OSM)
        missing = {**PHOTO, "lugar_ref": "https://www.openstreetmap.org/node/2",
                   "source_ref": "https://commons.wikimedia.org/wiki/File:Beta.jpg"}
        path = seed(tmp_path, PHOTO, missing)
        load_fotos.run(get_engine(), path)
        result = load_fotos.run(get_engine(), path)
        page = (await http.get("/api/v1/fotos")).json()
        bad = await http.get("/api/v1/fotos", params={"size": 500})

    assert result == {"loaded": 1, "sin_lugar": [missing["url"]]}
    assert db_session.scalar(select(func.count()).select_from(Foto)) == 1
    assert (page["total"], page["pages"]) == (1, 1)
    first = page["items"][0]
    assert (first["categoria_slug"], first["objeto_id"], first["nombre"]) == ("barberias", item, "Alfa")
    assert (first["autor"], first["licencia"], first["verified"]) == ("Ana", "CC BY 4.0", True)
    assert bad.status_code == 422


def test_acepta_fotos_de_mapillary_con_texto_alternativo_en_ingles(tmp_path: Path) -> None:
    mly = {**PHOTO, "source_ref": "https://www.mapillary.com/app/?pKey=123", "licencia": "CC BY-SA 4.0",
           "alt_text_en": "Street-level view of the Alfa barbershop"}
    assert load_fotos.read(seed(tmp_path, mly))[0]["alt_text_en"].startswith("Street-level")
    with pytest.raises(ValidationError):
        load_fotos.read(seed(tmp_path, {**mly, "alt_text_en": "x"}))


def test_la_semilla_de_mapillary_trae_autor_licencia_original_y_texto_en_ingles() -> None:
    fotos = load_fotos.read(load_fotos.SEED_MAPILLARY)
    assert len(fotos) == 199  # 201 elegidas menos 2 de parques eliminados (H35)
    assert all(f["url"].startswith("/assets/photos/mapillary/") and f["licencia"] == "CC BY-SA 4.0" for f in fotos)
    assert all(f["autor"] and f["source_ref"].startswith(load_fotos.MAPILLARY) and f["alt_text_en"] for f in fotos)
    assert all(f["lugar_ref"].startswith("https://www.openstreetmap.org/") for f in fotos)
