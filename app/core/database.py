"""Motor y sesiones de SQLAlchemy 2 (síncrono, psycopg 3).

Síncrono a propósito: el modo asíncrono de psycopg no admite el
ProactorEventLoop de Windows; FastAPI ejecuta las dependencias síncronas en
su threadpool.
"""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings


def build_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": settings.db_connect_timeout_s},
    )


@lru_cache
def get_engine() -> Engine:
    return build_engine(get_settings())


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """Dependencia de FastAPI: una sesión por petición, siempre cerrada."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
