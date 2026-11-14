"""Datos y repositorio de prueba para BaseCrudRepository (Centros Educativos)."""

from sqlalchemy.orm import Session

from app.models import CentroEducativo
from app.repositories.base_geo_repo import BaseCrudRepository

BIBLIOTECA = {"type": "Point", "coordinates": [-74.1547809, 4.6430253]}
CIUDAD_TINTAL = {"type": "Point", "coordinates": [-74.1577659, 4.6540182]}


def make_repo(session: Session) -> BaseCrudRepository[CentroEducativo]:
    return BaseCrudRepository(
        session, CentroEducativo,
        search_fields=("nombre", "direccion"),
        filter_fields=("tipo", "caracter", "verified"),
        sort_fields=("nombre", "id"),
    )


def seed_three(repo: BaseCrudRepository[CentroEducativo]) -> None:
    for nombre, tipo in [("Colegio Alfa", "colegio"), ("Jardín Beta 100%", "jardin"),
                         ("Colegio Gamma", "colegio")]:
        repo.create({"nombre": nombre, "tipo": tipo, "caracter": "publico"}, BIBLIOTECA)
