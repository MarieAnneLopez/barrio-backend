"""Hash de contraseñas, clave de firma y límite de intentos (H21, D58)."""

import pytest
from pydantic import SecretStr

from app.core import security
from app.core.config import Settings
from app.core.rate_limit import AttemptLimiter, TooManyAttemptsError


def test_hash_y_verificacion() -> None:
    hashed = security.hash_password("una-clave-larga")
    assert security.verify_password("una-clave-larga", hashed)
    assert not security.verify_password("otra", hashed)
    assert not security.verify_password("una-clave-larga", None)
    assert not security.verify_password("x" * 80, hashed)
    assert not security.verify_password("una-clave-larga", "no-es-un-hash")


@pytest.mark.parametrize("env, secret, error", [
    ("production", "", "obligatorio"),
    ("development", "corta", "32 caracteres"),
])
def test_clave_de_firma_exigida(monkeypatch: pytest.MonkeyPatch, env: str, secret: str, error: str) -> None:
    settings = Settings(environment=env, jwt_secret=SecretStr(secret))
    monkeypatch.setattr(security, "get_settings", lambda: settings)
    security.signing_key.cache_clear()
    try:
        with pytest.raises(RuntimeError, match=error):
            security.signing_key()
    finally:
        security.signing_key.cache_clear()


def test_clave_de_firma_configurada(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(environment="production", jwt_secret=SecretStr("k" * 40))
    monkeypatch.setattr(security, "get_settings", lambda: settings)
    security.signing_key.cache_clear()
    try:
        assert security.signing_key() == "k" * 40
        assert security.user_id_from_token(security.create_access_token(7)) == 7
    finally:
        security.signing_key.cache_clear()


def test_limitador_bloquea_y_se_libera_al_pasar_la_ventana() -> None:
    now = [0.0]
    limiter = AttemptLimiter(max_attempts=2, window_s=60, clock=lambda: now[0])
    limiter.hit("k")
    limiter.hit("k")
    with pytest.raises(TooManyAttemptsError) as blocked:
        limiter.check("k")
    assert blocked.value.details == {"retry_after_s": 61}
    limiter.check("otra")
    now[0] = 60.0
    limiter.check("k")
    limiter.hit("k")
    limiter.reset("k")
    limiter.check("k")
