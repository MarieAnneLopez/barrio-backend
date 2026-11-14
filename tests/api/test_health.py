from httpx import AsyncClient


async def test_health_contra_postgis_real(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["postgis"].split(".")[0].isdigit()


async def test_health_degradado_responde_503(client_db_down: AsyncClient) -> None:
    response = await client_db_down.get("/api/v1/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unavailable", "postgis": None}


async def test_cabeceras_de_seguridad(client: AsyncClient) -> None:
    headers = (await client.get("/api/v1/health")).headers

    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["content-security-policy"].startswith("default-src 'none'")


async def test_la_documentacion_no_lleva_la_csp_cerrada(client: AsyncClient) -> None:
    response = await client.get("/docs")

    assert response.status_code == 200
    assert "content-security-policy" not in response.headers
    assert response.headers["x-content-type-options"] == "nosniff"


async def test_cors_permite_el_frontend_y_rechaza_otros_origenes(client: AsyncClient) -> None:
    preflight = {"Access-Control-Request-Method": "GET"}
    allowed = await client.options(
        "/api/v1/health", headers={"Origin": "http://localhost:5173", **preflight}
    )
    denied = await client.options(
        "/api/v1/health", headers={"Origin": "https://evil.example", **preflight}
    )

    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-origin" not in denied.headers
