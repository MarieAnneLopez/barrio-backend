"""H35: sincroniza nombre y descripciones por source_ref y aplica las eliminaciones."""

import json
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_engine
from app.models import Calificacion, Foto
from etl import sync_places
from tests.api.crud_app import BASE, colegio, crud_app
from tests.conftest import make_client

pytestmark = pytest.mark.usefixtures("db_session")
OSM = "https://www.openstreetmap.org/way/{}"


def seed(tmp: Path, features: list[dict[str, object]], gone: list[dict[str, object]]) -> Path:
    (tmp / "modules").mkdir()
    fc = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": p, "geometry": None} for p in features]}
    (tmp / "modules" / "centros-educativos.geojson").write_text(json.dumps(fc), encoding="utf-8")
    (tmp / "eliminados.json").write_text(json.dumps({"eliminados": gone}), encoding="utf-8")
    return tmp


async def test_retiro_unico_conserva_relaciones_y_otras_fichas(tmp_path: Path, db_session: Session) -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        for name, ref in [("Viejo", OSM.format(1)), ("Borrar", OSM.format(2)), ("Ejemplo 1", "dato de ejemplo"),
                          ("Ejemplo 2", "dato de ejemplo")]:
            item = (await http.post(BASE, json={**colegio(name), "source_ref": ref})).json()
        db_session.add_all([Foto(categoria_slug="centros-educativos", objeto_id=item["id"] - 2, url="/assets/photos/x.webp",
                                 alt_text="Foto", orden=0),
                            Calificacion(categoria_slug="centros-educativos", objeto_id=item["id"] - 2, estrellas=4)])
        db_session.commit()
        path = seed(tmp_path, [
            {"nombre": "Nuevo", "source_ref": OSM.format(1), "descripcion_es": "Colegio.", "descripcion_en": "School."},
            {"nombre": "Ejemplo 2", "source_ref": "dato de ejemplo", "descripcion_es": "Dato de ejemplo.", "descripcion_en": "Sample."},
        ], [{"modulo": "centros-educativos", "feature": {"properties": {"source_ref": OSM.format(2)}}}])
        first = sync_places.run(get_engine(), path)
        again = sync_places.run(get_engine(), path)
        names = sorted(i["nombre"] for i in (await http.get(BASE)).json()["items"])

    assert first == {"retirados": 1} and again == {"retirados": 0}
    assert names == ["Ejemplo 1", "Ejemplo 2", "Viejo"]
    assert db_session.scalar(select(func.count()).select_from(Foto)) == 1
    assert db_session.scalar(select(func.count()).select_from(Calificacion)) == 1
