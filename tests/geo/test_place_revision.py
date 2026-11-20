"""Una revisión cambia solo los campos que administración no ha editado."""
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CentroEducativo
from etl import bootstrap
from tests.geo.test_seed_rollout import bundle, schools  # noqa: F401


def test_edicion_de_un_campo_conserva_su_id_y_actualiza_el_otro(db_session: Session, bundle: Path) -> None:
    schools(bundle, "Viejo", "Otra escuela")
    bootstrap.main()
    row, removed = db_session.scalars(select(CentroEducativo).order_by(CentroEducativo.id)).all()
    school_id = row.id
    row.descripcion_es = "Descripción editorial"
    db_session.delete(removed)
    db_session.commit()
    schools(bundle, "Nuevo", "Escuela retirada")
    bootstrap.main()
    db_session.expire_all()
    assert [(r.id, r.nombre, r.descripcion_es) for r in db_session.scalars(select(CentroEducativo))] == [
        (school_id, "Nuevo", "Descripción editorial")]
