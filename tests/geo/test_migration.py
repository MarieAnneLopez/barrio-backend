"""La migración inicial crea el esquema PostGIS completo y se revierte limpia."""

from collections.abc import Iterator

import pytest
from sqlalchemy import Connection, create_engine, text

from app.core.config import Settings
from tests.db_setup import alembic, drop_database, ensure_database

DB = "barrio_migration_test"
MODULE_TABLES = {
    "centros_educativos": "POINT", "escenarios_deportivos": "POLYGON",
    "camaras_seguridad": "POINT", "zonas_verdes": "POLYGON",
    "datos_catastrales": "POLYGON", "estado_calles": "LINESTRING",
    "estaciones_transporte": "POINT", "sitios_comida": "POINT", "librerias": "POINT",
    "robos": "POINT", "localidad_kennedy": "MULTIPOLYGON", "atencion_inmediata": "POINT",
    "veterinarias": "POINT", "barberias": "POINT",
}
TRANSVERSAL = {"usuarios", "calificaciones", "fotos", "historia_hitos"}  # faq_items se retiró (D65)
AUDIT = {"source_type", "source_ref", "verified", "created_at", "updated_at"}


@pytest.fixture(scope="module")
def conn() -> Iterator[Connection]:
    drop_database(DB)
    ensure_database(DB)
    alembic("upgrade", "head", database=DB)
    # AUTOCOMMIT: sin transacciones abiertas que bloqueen los DROP del downgrade.
    engine = create_engine(Settings(postgres_db=DB).database_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as connection:
        yield connection
    engine.dispose()
    drop_database(DB)


def _tables(conn: Connection) -> set[str]:
    sql = text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
    return set(conn.execute(sql).scalars())


def test_crea_las_14_tablas_y_las_transversales(conn: Connection) -> None:
    assert set(MODULE_TABLES) | TRANSVERSAL <= _tables(conn)


@pytest.mark.parametrize("table", MODULE_TABLES)
def test_geometria_srid_4326_con_indice_gist(conn: Connection, table: str) -> None:
    geo = conn.execute(
        text("SELECT type, srid FROM geometry_columns WHERE f_table_name = :t AND f_geometry_column = 'geom'"),
        {"t": table},
    ).one()
    gist = conn.execute(
        text("SELECT count(*) FROM pg_indexes WHERE tablename = :t AND indexdef ILIKE '%USING gist (geom)%'"),
        {"t": table},
    ).scalar()
    columns = set(conn.execute(
        text("SELECT column_name FROM information_schema.columns WHERE table_name = :t"), {"t": table}
    ).scalars())
    assert (geo.type, geo.srid) == (MODULE_TABLES[table], 4326)
    assert gist == 1
    assert AUDIT <= columns


def test_las_restricciones_rechazan_datos_invalidos(conn: Connection) -> None:
    with pytest.raises(Exception, match="ck_calificaciones_estrellas"):
        conn.execute(text(
            "INSERT INTO calificaciones (categoria_slug, objeto_id, estrellas) VALUES ('robos', 1, 4.3)"
        ))


def test_downgrade_deja_la_base_sin_tablas_del_proyecto(conn: Connection) -> None:
    alembic("downgrade", "base", database=DB)
    assert not (set(MODULE_TABLES) | TRANSVERSAL) & _tables(conn)
    alembic("upgrade", "head", database=DB)
    assert set(MODULE_TABLES) <= _tables(conn)
