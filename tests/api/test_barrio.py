from pathlib import Path

from fastapi import FastAPI
from httpx import AsyncClient

from app.api.deps import get_barrio_repository
from app.repositories.barrio_repository import GeoJsonBarrioRepository
from tests.conftest import make_client


async def test_poligono_es_un_feature_geojson_con_bbox(client: AsyncClient) -> None:
    response = await client.get("/api/v1/barrio/poligono")

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "Feature"
    assert body["geometry"]["type"] == "MultiPolygon"
    xmin, ymin, xmax, ymax = body["bbox"]
    assert xmin < xmax and ymin < ymax
    assert body["properties"]["nombre"] == "El Tintal"
    assert body["properties"]["verified"] is True
    assert body["properties"]["definicion"] == "UPZ 78 Tintal Norte + UPZ 79 Calandaima"


async def test_sin_semilla_responde_503_con_formato_de_error(app: FastAPI, tmp_path: Path) -> None:
    missing = GeoJsonBarrioRepository(tmp_path / "no-existe.geojson")
    app.dependency_overrides[get_barrio_repository] = lambda: missing

    async with make_client(app) as http:
        response = await http.get("/api/v1/barrio/poligono")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SEED_UNAVAILABLE"


async def test_capas_base_son_feature_collections(client: AsyncClient) -> None:
    response = await client.get("/api/v1/barrio/capas/parques")

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "FeatureCollection" and body["features"]
    assert body["license"].startswith("© OpenStreetMap")


async def test_capa_desconocida_o_ruta_libre_da_422(client: AsyncClient) -> None:
    unknown = await client.get("/api/v1/barrio/capas/usuarios")
    traversal = await client.get("/api/v1/barrio/capas/..%2F..%2F.env")

    assert unknown.status_code == 422
    assert traversal.status_code in (404, 422)
