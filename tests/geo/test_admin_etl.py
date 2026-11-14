"""Paso «admin» del ETL: crea o actualiza la cuenta de administración (H21, D58)."""

import pytest
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import get_engine
from app.core.security import verify_password
from app.models.usuario import Usuario
from app.repositories.usuario_repository import EmailTakenError
from app.schemas.auth import RegisterIn
from app.services.auth_service import AuthService, EmailInUseError
from etl import admin
from tests.api.auth_helpers import make_user


def _settings(email: str = "Marie@Eltintal.local", password: str = "clave-admin-larga") -> Settings:
    return Settings(admin_email=email, admin_password=SecretStr(password), admin_nombre="Marie")


def test_sin_variables_no_hace_nada(db_session: Session) -> None:
    result = admin.run(get_engine(), Settings(admin_email="", admin_password=SecretStr("")))
    assert result["admin"].startswith("omitido") and db_session.scalar(select(Usuario)) is None


def test_crea_y_luego_actualiza_la_cuenta(db_session: Session) -> None:
    make_user(db_session, "marie@eltintal.local", activo=False)

    first = admin.run(get_engine(), _settings())
    second = admin.run(get_engine(), _settings(password="otra-clave-admin"))

    assert first["admin"] == "actualizada marie@eltintal.local" and second["admin"].startswith("actualizada")
    db_session.expire_all()
    user = db_session.scalars(select(Usuario)).one()
    assert (user.rol, user.activo, user.nombre) == ("admin", True, "Marie")
    assert verify_password("otra-clave-admin", user.password_hash)


def test_crea_si_no_existe(db_session: Session) -> None:
    assert admin.run(get_engine(), _settings())["admin"] == "creada marie@eltintal.local"


def test_rechaza_clave_corta() -> None:
    with pytest.raises(ValueError, match="12 caracteres"):
        admin.run(get_engine(), _settings(password="corta123"))


def test_correo_repetido_en_carrera(db_session: Session) -> None:
    """Dos registros a la vez: el índice único decide y el servicio responde 409."""
    make_user(db_session, "doble@prueba.co")
    with pytest.raises(EmailTakenError):
        make_user(db_session, "doble@prueba.co")

    class RacingStore:
        def by_email(self, email: str) -> None:
            return None

        def add(self, usuario: Usuario) -> Usuario:
            raise EmailTakenError

    data = RegisterIn(nombre="X", email="doble@prueba.co", password=SecretStr("una-clave-larga"))
    with pytest.raises(EmailInUseError):
        AuthService(RacingStore()).register(data)  # type: ignore[arg-type]
