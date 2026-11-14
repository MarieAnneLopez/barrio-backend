"""Recursos de datos abiertos usados por el ETL (consultados el 2026-11-14, D4/D51).

Cada entrada guarda la URL de descarga (lo que se lee), la página del conjunto
(lo que se cita en source_ref), la entidad y la licencia.
"""

from dataclasses import dataclass

PORTAL = "https://datosabiertos.bogota.gov.co/dataset/"


@dataclass(frozen=True)
class Source:
    url: str
    page: str
    entity: str
    license: str


NUSE_123 = Source(
    PORTAL + "9bdf518e-b756-4865-983f-0521111fbcd1/resource/30d65a8b-d0ed-4e95-977e-0d7cc2ea89ef"
    "/download/datos-abiertllamadastramitadas-c4-",
    PORTAL + "incidentes", "Secretaría Distrital de Seguridad, Convivencia y Justicia",
    "CC BY-SA 4.0")
CAI = Source(
    PORTAL + "bcc51101-762b-4e13-9455-f77502c75a0f/resource/202c5810-6880-43f8-b801-df70aaf6d237"
    "/download/comandoatencioninmediata",
    PORTAL + "centro-de-atencion-accion-para-bogota-d-c",
    "Secretaría Distrital de Seguridad, Convivencia y Justicia", "CC BY-SA 4.0")
IPS = Source(
    PORTAL + "fc66362f-ba91-4d7a-af9c-d0b3d3a60106/resource/0e432b79-8c0f-4a0c-a592-43330712fe03"
    "/download/ips.geojson",
    PORTAL + "instituciones-prestadoras-de-salud-bogota", "Secretaría Distrital de Salud",
    "CC BY 4.0")
LOTE = Source(
    PORTAL + "f615a894-3460-4a86-ae9e-fa6e6bf35e77/resource/3c3ca2b9-f23e-4932-bf40-db11b8c260df"
    "/download/lote.gpkg.10.26.zip",
    PORTAL + "lote", "Unidad Administrativa Especial de Catastro Distrital", "CC BY 4.0")
ESTRATO = Source(
    PORTAL + "55467552-0af4-4524-a390-a2956035744e/resource/cde22374-35e8-4c7d-abf9-903cd82faa42"
    "/download/manzanaestratificacion.gpkg",
    PORTAL + "estratificacion-para-bogota", "Secretaría Distrital de Planeación", "CC BY 4.0")
POBLACION = Source(
    PORTAL + "85bf790d-84d1-4eda-bd6f-40af62e71d95/resource/37e58cb3-c870-4608-8c37-ce45db0eb7c1"
    "/download/osb_demografia-poblacion-localidad",
    PORTAL + "piramide-poblacional-bogota-d-c", "Secretaría Distrital de Salud", "CC BY 4.0")
ALCALDIA = Source(
    PORTAL + "a1749d04-df90-427d-ac51-7d2dc3f7d984/resource/576c7c25-6b02-437c-b7d9-bdc4ea1a86db"
    "/download/alcaldialocaljson.zip",
    PORTAL + "alcaldia-local-bogota-d-c", "Secretaría Distrital de Gobierno", "CC BY-SA 4.0")
