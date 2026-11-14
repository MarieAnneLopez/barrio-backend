"""BaseCrudRepository (escritura) sobre PostGIS real."""

from sqlalchemy.orm import Session

from tests.geo.crud_helpers import CIUDAD_TINTAL, make_repo, seed_three


def test_actualiza_parcial_y_geometria(db_session: Session) -> None:
    repo = make_repo(db_session)
    seed_three(repo)

    record = repo.update(1, {"telefono": "6011234567"}, CIUDAD_TINTAL)

    assert record is not None
    assert record.entity.telefono == "6011234567" and record.entity.nombre == "Colegio Alfa"
    assert record.geometry == CIUDAD_TINTAL


def test_actualizar_inexistente_devuelve_none(db_session: Session) -> None:
    assert make_repo(db_session).update(99, {"telefono": "1"}, None) is None


def test_elimina_y_reporta_inexistentes(db_session: Session) -> None:
    repo = make_repo(db_session)
    seed_three(repo)

    assert repo.delete(2) is True
    assert repo.get(2) is None
    assert repo.delete(2) is False
