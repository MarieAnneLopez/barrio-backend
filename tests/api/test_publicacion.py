"""H35: despublicar oculta un lugar en la plataforma sin borrar la fila; descripción ES/EN."""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CentroEducativo
from tests.api.crud_app import BASE, colegio, crud_app
from tests.conftest import make_client

pytestmark = pytest.mark.usefixtures("db_session")


async def test_despublicado_no_se_lista_ni_se_abre_pero_la_fila_sigue(db_session: Session) -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        visible = (await http.post(BASE, json={**colegio("Colegio Visible"),
                                               "descripcion_es": "Colegio público.",
                                               "descripcion_en": "Public school."})).json()
        hidden = (await http.post(BASE, json={**colegio("Colegio Oculto"), "publicado": False})).json()
        names = [i["nombre"] for i in (await http.get(BASE)).json()["items"]]
        features = (await http.get(f"{BASE}/geojson")).json()["features"]
        detail = await http.get(f"{BASE}/{hidden['id']}")

    assert hidden["publicado"] is False  # la escritura del admin sí lo devuelve
    assert visible["descripcion_es"] == "Colegio público." and visible["descripcion_en"] == "Public school."
    assert names == ["Colegio Visible"] and len(features) == 1
    assert detail.status_code == 404
    row = db_session.scalars(select(CentroEducativo).where(CentroEducativo.id == hidden["id"])).one()
    assert row.nombre == "Colegio Oculto" and row.publicado is False


async def test_volver_a_publicar_lo_muestra_otra_vez() -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        hidden = (await http.post(BASE, json={**colegio("Colegio Vuelve"), "publicado": False})).json()
        patched = await http.patch(f"{BASE}/{hidden['id']}", json={"publicado": True})
        detail = await http.get(f"{BASE}/{hidden['id']}")

    assert patched.json()["publicado"] is True and detail.status_code == 200


async def test_acepta_la_fuente_sitio_oficial() -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        created = await http.post(BASE, json={**colegio("Colegio Oficial"), "source_type": "sitio_oficial",
                                              "source_ref": "https://example.org/directorio", "verified": True})
        wrong = await http.post(BASE, json={**colegio("Colegio X"), "source_type": "google_maps"})

    assert created.status_code == 201 and created.json()["source_type"] == "sitio_oficial"
    assert wrong.status_code == 422
