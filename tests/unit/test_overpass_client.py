import httpx
import pytest

from etl.overpass import OverpassClient, OverpassError

OK = {"osm3s": {"timestamp_osm_base": "2026-11-14T06:44:36Z"}, "elements": [{"id": 1}]}


def _client(handler, retries: int = 3) -> OverpassClient:
    http = httpx.Client(transport=httpx.MockTransport(handler))
    return OverpassClient(http=http, retries=retries, backoff_s=0)


def test_devuelve_los_elementos_validados() -> None:
    client = _client(lambda request: httpx.Response(200, json=OK))

    assert client.query("[out:json];node(1);out;")["elements"] == [{"id": 1}]


def test_reintenta_ante_429_y_5xx() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(429 if len(calls) == 1 else 504 if len(calls) == 2 else 200, json=OK)

    assert _client(handler).query("q")["elements"] == [{"id": 1}]
    assert len(calls) == 3


def test_reintenta_ante_timeout_y_se_rinde() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("lento", request=request)

    with pytest.raises(OverpassError, match="3 intentos"):
        _client(handler).query("q")


def test_no_reintenta_un_400_de_consulta_mala() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(400, text="parse error")

    with pytest.raises(OverpassError, match="400"):
        _client(handler).query("q")
    assert len(calls) == 1


def test_rechaza_respuestas_sin_lista_de_elementos() -> None:
    client = _client(lambda request: httpx.Response(200, json={"remark": "runtime error"}))

    with pytest.raises(OverpassError, match="elements"):
        client.query("q")


def test_envia_user_agent_identificable() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["ua"] = request.headers["user-agent"]
        return httpx.Response(200, json=OK)

    _client(handler).query("q")
    assert seen["ua"].startswith("barrio-etl/")
