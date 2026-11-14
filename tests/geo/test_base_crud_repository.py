"""BaseCrudRepository (lectura) sobre PostGIS real, con Centros Educativos."""

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.repositories.query import ListQuery
from tests.geo.crud_helpers import BIBLIOTECA, make_repo, seed_three


def test_crea_y_devuelve_la_geometria_en_geojson(db_session: Session) -> None:
    record = make_repo(db_session).create(
        {"nombre": "Colegio Alfa", "tipo": "colegio", "caracter": "publico"}, BIBLIOTECA
    )

    assert record.entity.id == 1
    assert record.geometry == BIBLIOTECA
    assert record.entity.source_type == "seed" and record.entity.verified is False


def test_lista_paginada_con_total(db_session: Session) -> None:
    repo = make_repo(db_session)
    seed_three(repo)

    page = repo.list(ListQuery(page=2, size=2, sort="nombre"))

    assert page.total == 3 and page.pages == 2
    assert [r.entity.nombre for r in page.items] == ["Jardín Beta 100%"]


def test_busqueda_trata_comodines_como_texto(db_session: Session) -> None:
    repo = make_repo(db_session)
    seed_three(repo)

    assert [r.entity.nombre for r in repo.list(ListQuery(q="100%")).items] == ["Jardín Beta 100%"]
    assert repo.list(ListQuery(q="_")).total == 0


def test_filtros_y_orden_descendente(db_session: Session) -> None:
    repo = make_repo(db_session)
    seed_three(repo)

    page = repo.list(ListQuery(filters={"tipo": "colegio", "verified": "false"}, sort="-nombre"))

    assert [r.entity.nombre for r in page.items] == ["Colegio Gamma", "Colegio Alfa"]


def test_rechaza_orden_y_filtros_no_permitidos(db_session: Session) -> None:
    repo = make_repo(db_session)
    with pytest.raises(AppError, match="sort"):
        repo.list(ListQuery(sort="telefono"))
    with pytest.raises(AppError, match="verified"):
        repo.list(ListQuery(filters={"verified": "quizas"}))


def test_features_devuelve_todo_lo_filtrado(db_session: Session) -> None:
    repo = make_repo(db_session)
    seed_three(repo)

    features = repo.features(ListQuery(filters={"tipo": "colegio"}))

    assert len(features) == 2 and all(f.geometry == BIBLIOTECA for f in features)
