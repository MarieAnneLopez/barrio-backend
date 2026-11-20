"""Arranque de producción (D62): semillas solo si la base está vacía; historia y admin siempre."""

from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import get_engine
from app.models import CentroEducativo
from etl import admin, bootstrap


def test_carga_una_vez_y_conserva_los_id(db_session: Session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    settings = Settings(admin_email="demo@prueba.co", admin_password=SecretStr("clave-de-prueba-larga"))
    monkeypatch.setattr(admin, "get_settings", lambda: settings)
    monkeypatch.setattr(bootstrap, "get_settings", lambda: settings)
    assert bootstrap.is_empty(get_engine())

    first = bootstrap.main()
    ids = set(db_session.scalars(select(CentroEducativo.id)))
    second = bootstrap.main()
    db_session.expire_all()

    assert first["semillas"] != "ya cargadas" and second["semillas"] == "ya cargadas"
    assert ids and ids == set(db_session.scalars(select(CentroEducativo.id)))
    assert db_session.scalar(select(func.count()).select_from(CentroEducativo)) == len(ids)
    assert str(second["admin"]["admin"]).startswith("actualizada")  # type: ignore[index]
    assert not bootstrap.is_empty(get_engine())
    db_session.query(CentroEducativo).delete()
    db_session.commit()
    third = bootstrap.main()  # vaciar un módulo ya cargado es una baja editorial
    assert third["semillas"] == "ya cargadas"
    assert db_session.scalar(select(func.count()).select_from(CentroEducativo)) == 0
    forced = bootstrap.load_missing(get_engine(), {"barberias"})
    assert list(forced) == ["barberias"]  # type: ignore[call-overload]
