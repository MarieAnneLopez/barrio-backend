from sqlalchemy import Column, Index, Integer, MetaData, String, Table, UniqueConstraint

from app.models.base import NAMING_CONVENTION, SRID, Base


def test_srid_oficial_es_wgs84() -> None:
    assert SRID == 4326


def test_la_convencion_da_nombres_estables_a_restricciones() -> None:
    metadata = MetaData(naming_convention=Base.metadata.naming_convention)
    table = Table(
        "lugares",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("nombre", String(120)),
        UniqueConstraint("nombre"),
        Index(None, "nombre"),
    )

    names = {c.name for c in table.constraints} | {i.name for i in table.indexes}

    assert {"pk_lugares", "uq_lugares_nombre", "ix_lugares_nombre"} <= names
    assert Base.metadata.naming_convention == NAMING_CONVENTION
