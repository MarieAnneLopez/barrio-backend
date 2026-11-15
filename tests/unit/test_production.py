"""Configuración de producción (D62): URL de la base, IP tras el proxy, admin y clave de firma."""

from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from app.core import client_ip, security
from app.core.config import Settings
from app.main import create_app
from etl import admin


def test_database_url_del_proveedor_usa_psycopg() -> None:
    settings = Settings(DATABASE_URL=SecretStr("postgresql://u:p@ep-x.neon.tech/barrio?sslmode=require"))
    url = settings.database_url
    assert (url.drivername, url.host, url.query["sslmode"]) == ("postgresql+psycopg", "ep-x.neon.tech", "require")
    assert Settings(DATABASE_URL=SecretStr("")).database_url.host == "127.0.0.1"


def request(headers: dict[str, str], host: str = "10.0.0.9") -> SimpleNamespace:
    return SimpleNamespace(headers=headers, client=SimpleNamespace(host=host))


@pytest.mark.parametrize("headers, expected", [
    ({"x-proxy-secret": "s" * 32, "x-client-ip": "190.1.2.3"}, "190.1.2.3"),
    ({"x-proxy-secret": "otra", "x-client-ip": "190.1.2.3"}, "10.0.0.9"),
    ({"x-client-ip": "190.1.2.3"}, "10.0.0.9"),
    ({"x-proxy-secret": "s" * 32}, "10.0.0.9"),
])
def test_solo_el_proxy_con_clave_puede_decir_la_ip(monkeypatch: pytest.MonkeyPatch, headers: dict[str, str],
                                                  expected: str) -> None:
    monkeypatch.setattr(client_ip, "get_settings", lambda: Settings(proxy_secret=SecretStr("s" * 32)))
    assert client_ip.client_key(request(headers)) == expected  # type: ignore[arg-type]


def test_sin_clave_de_proxy_se_usa_la_conexion(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client_ip, "get_settings", lambda: Settings(proxy_secret=SecretStr("")))
    assert client_ip.client_key(request({"x-proxy-secret": "", "x-client-ip": "1.1.1.1"})) == "10.0.0.9"  # type: ignore[arg-type]


def test_en_produccion_rechaza_la_clave_de_demostracion(tmp_path: Path) -> None:
    demo = admin.demo_password()
    assert demo and len(demo) >= 12
    settings = Settings(environment="production", admin_email="a@b.co", admin_password=SecretStr(demo))
    with pytest.raises(ValueError, match="demostración"):
        admin.run(None, settings)  # type: ignore[arg-type]
    assert admin.demo_password(tmp_path / "no-existe") is None
    example = tmp_path / ".env.example"
    example.write_text("ADMIN_PASSWORD=\n", encoding="utf-8")
    assert admin.demo_password(example) is None


def test_en_produccion_la_api_no_arranca_sin_clave_de_firma(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(security, "get_settings", lambda: Settings(environment="production", jwt_secret=SecretStr("")))
    security.signing_key.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="JWT_SECRET"):
            create_app(Settings(environment="production"))
    finally:
        security.signing_key.cache_clear()
