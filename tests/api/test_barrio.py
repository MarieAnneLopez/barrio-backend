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
