"""Los borradores solo se leen desde administración y no ocupan páginas públicas."""

from types import SimpleNamespace

import pytest
from sqlalchemy.orm import Session

from app.api.guards import current_user
from app.models import Foto
from tests.api.crud_app import BASE, colegio, crud_app
from tests.conftest import make_client

pytestmark = pytest.mark.usefixtures("db_session")


async def test_lectura_admin_requiere_rol_y_permite_buscar_borradores() -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        await http.post(BASE, json=colegio("Público"))
        draft = (await http.post(BASE, json=colegio("Oculto", publicado=False))).json()
        route = f"{BASE}/admin"
        assert (await http.get(route, params={"q": "Oculto"})).json()["items"] == [draft]
        assert (await http.get(f"{route}/{draft['id']}")).json() == draft
        assert (await http.get(f"{BASE}/{draft['id']}")).status_code == 404

    app = crud_app(as_admin=False)
    async with make_client(app) as http:
        assert (await http.get(route)).status_code == 401
        assert (await http.get(f"{route}/{draft['id']}")).status_code == 401
        app.dependency_overrides[current_user] = lambda: SimpleNamespace(rol="visitante")
        assert (await http.get(route)).status_code == 403
        assert (await http.get(f"{route}/{draft['id']}")).status_code == 403


async def test_pagina_galeria_cuenta_solo_fotos_publicas_con_lugar(db_session: Session) -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        for name, published in [("Oculto", False), ("Primero", True), ("Segundo", True)]:
            await http.post(BASE, json=colegio(name, publicado=published))
        db_session.add_all(Foto(categoria_slug="centros-educativos", objeto_id=id_,
                                url=f"/assets/photos/{id_}.webp", alt_text="Foto")
                           for id_ in (1, 2, 3, 99))
        db_session.commit()
        pages = [(await http.get("/api/v1/fotos", params={"size": 1, "page": n})).json()
                 for n in (1, 2, 3)]
    assert [(p["total"], p["pages"]) for p in pages] == [(2, 2)] * 3
    assert [[item["nombre"] for item in p["items"]] for p in pages] == [["Primero"], ["Segundo"], []]
