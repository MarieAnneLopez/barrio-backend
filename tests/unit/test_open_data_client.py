"""Cliente de datos abiertos: lista blanca de hosts (D4), caché y reintentos."""

from pathlib import Path

import httpx
import pytest

from etl.datos_abiertos.client import OpenDataClient, OpenDataError, read_text

URL = "https://datosabiertos.bogota.gov.co/dataset/x/download/a.csv"


def _client(tmp_path: Path, handler) -> OpenDataClient:  # noqa: ANN001
    http = httpx.Client(transport=httpx.MockTransport(handler))
    return OpenDataClient(http=http, cache_dir=tmp_path, backoff_s=0)


@pytest.mark.parametrize("url", ["https://example.com/a.csv", "http://datosabiertos.bogota.gov.co/a"])
def test_rechaza_hosts_no_autorizados_y_http_plano(tmp_path: Path, url: str) -> None:
    with pytest.raises(OpenDataError):
        _client(tmp_path, lambda r: httpx.Response(200)).fetch(url)


def test_descarga_una_vez_y_luego_usa_la_cache(tmp_path: Path) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url)
        return httpx.Response(200, content=b"A;B\n1;2\n")

    client = _client(tmp_path, handler)
    first, second = client.fetch(URL), client.fetch(URL)

    assert first == second and first.read_bytes() == b"A;B\n1;2\n" and len(calls) == 1


def test_reintenta_errores_transitorios(tmp_path: Path) -> None:
    answers = iter([httpx.Response(503), httpx.Response(200, content=b"ok")])
    assert _client(tmp_path, lambda r: next(answers)).fetch(URL).read_bytes() == b"ok"


def test_falla_tras_los_reintentos_o_ante_un_404(tmp_path: Path) -> None:
    with pytest.raises(OpenDataError, match="3 intentos"):
        _client(tmp_path, lambda r: httpx.Response(502)).fetch(URL)
    with pytest.raises(OpenDataError, match="404"):
        _client(tmp_path / "b", lambda r: httpx.Response(404)).fetch(URL)


def test_error_de_red_cuenta_como_intento(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sin red")

    with pytest.raises(OpenDataError, match="ConnectError"):
        _client(tmp_path, handler).fetch(URL)


def test_read_text_acepta_utf8_y_windows_1252(tmp_path: Path) -> None:
    utf, ansi = tmp_path / "u", tmp_path / "w"
    utf.write_bytes("﻿Policía".encode())
    ansi.write_bytes("Policía".encode("cp1252"))

    assert read_text(utf) == read_text(ansi) == "Policía"
