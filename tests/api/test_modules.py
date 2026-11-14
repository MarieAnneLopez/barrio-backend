"""Los 14 módulos salen de la misma fábrica: mismo contrato, reglas propias de cada uno."""

import pytest
from sqlalchemy.orm import Session

from app.modules.registry import MODULES
from tests.api.crud_app import crud_app
from tests.api.module_payloads import GEOMETRY, PATCHES, PAYLOADS, POINT, payload
from tests.conftest import make_client

pytestmark = pytest.mark.usefixtures("db_session")
SLUGS = [m.slug for m in MODULES]


def test_registro_expone_los_catorce_modulos() -> None:
    assert len(SLUGS) == 14 and sorted(SLUGS) == sorted(PAYLOADS)


@pytest.mark.parametrize("slug", SLUGS)
async def test_crud_completo_por_fabrica(slug: str) -> None:
    field, value = PATCHES[slug]
    base = f"/api/v1/{slug}"
    async with make_client(crud_app(as_admin=True)) as http:
        created = await http.post(base, json=payload(slug))
        item_id = created.json()["id"]
        page = await http.get(base)
        collection = await http.get(f"{base}/geojson")
        patched = await http.patch(f"{base}/{item_id}", json={field: value})
        deleted = await http.delete(f"{base}/{item_id}")
        missing = await http.get(f"{base}/{item_id}")

    assert created.status_code == 201, created.json()
    assert created.json()["geometry"] == GEOMETRY.get(slug, POINT)
    assert created.json()["source_type"] == "seed"
    assert page.json()["total"] == 1
    assert collection.json()["features"][0]["id"] == item_id
    assert patched.json()[field] == value
    assert (deleted.status_code, missing.status_code) == (204, 404)


@pytest.mark.parametrize("slug", SLUGS)
async def test_escrituras_exigen_admin(slug: str) -> None:
    async with make_client(crud_app(as_admin=False)) as http:
        response = await http.post(f"/api/v1/{slug}", json=payload(slug))

    assert response.status_code == 401


async def test_codigo_de_camara_repetido_es_conflicto() -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        await http.post("/api/v1/camaras-seguridad", json=payload("camaras-seguridad"))
        again = await http.post("/api/v1/camaras-seguridad", json=payload("camaras-seguridad"))

    assert again.status_code == 409 and again.json()["error"]["code"] == "CONFLICT"


@pytest.mark.parametrize(("slug", "bad"), [
    ("robos", {"cantidad": -1}), ("robos", {"franja_horaria": "mediodia"}),
    ("sitios-comida", {"rango_precios": "$$$$"}), ("atencion-inmediata", {"tipo": "farmacia"}),
    ("estaciones-transporte", {"tipo": "metro"}), ("camaras-seguridad", {"codigo": "X"}),
    ("veterinarias", {"geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}}),
    ("datos-catastrales", {"estrato": 7}), ("datos-catastrales", {"matricula_inmobiliaria": "50C 1"}),
    ("zonas-verdes", {"tipo": "bosque"}), ("estado-calles", {"geometry": POINT}),
    ("localidad", {"bandera_url": "https://example.com/bandera.png"}),
    ("escenarios-deportivos", {"acceso": "gratis"}),
])
async def test_valores_fuera_del_dominio_son_422(slug: str, bad: dict) -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        response = await http.post(f"/api/v1/{slug}", json=payload(slug, **bad))

    assert response.status_code == 422


async def test_robos_sin_franja_y_filtrados_por_fecha(db_session: Session) -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        await http.post("/api/v1/robos", json=payload("robos"))
        await http.post("/api/v1/robos", json=payload("robos", fecha="2024-05-01"))
        page = await http.get("/api/v1/robos", params={"fecha": "2025-02-01", "sort": "-cantidad"})

    [item] = page.json()["items"]
    assert item["franja_horaria"] is None and item["cantidad"] == 3


async def test_ficha_de_localidad_sin_geometria_y_calle_por_verificar() -> None:
    async with make_client(crud_app(as_admin=True)) as http:
        ficha = await http.post("/api/v1/localidad", json={"nombre_localidad": "Kennedy"})
        calle = await http.post("/api/v1/estado-calles", json=payload("estado-calles"))

    assert ficha.status_code == 201 and ficha.json()["geometry"] is None
    assert calle.json()["estado"] is None


def test_cada_modulo_ordena_por_su_campo_de_etiqueta() -> None:
    """El frontend ordena la lista por el campo que nombra cada registro."""
    assert all(m.label_field in m.sort_fields for m in MODULES)
