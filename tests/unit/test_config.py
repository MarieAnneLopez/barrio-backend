import pytest

from app.core.config import Settings


def test_la_url_usa_psycopg_y_no_imprime_la_clave() -> None:
    settings = Settings(postgres_password="super-secreta", postgres_host="db", postgres_port=5433)

    url = settings.database_url

    assert url.drivername == "postgresql+psycopg"
    assert url.host == "db" and url.port == 5433
    assert "super-secreta" not in str(url)
    assert "super-secreta" not in repr(settings)


def test_cors_se_lee_como_lista_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", '["http://a.test", "http://b.test"]')

    assert Settings().cors_origins == ["http://a.test", "http://b.test"]


def test_docs_se_apagan_en_produccion() -> None:
    assert Settings(environment="development").docs_enabled is True
    assert Settings(environment="production").docs_enabled is False
