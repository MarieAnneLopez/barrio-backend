"""Modelos SQLAlchemy/GeoAlchemy2 (SRID 4326).

Importarlos aquí registra todas las tablas en Base.metadata (Alembic).
"""

from app.models.atencion_inmediata import AtencionInmediata
from app.models.barberia import Barberia
from app.models.calificacion import Calificacion
from app.models.camara_seguridad import CamaraSeguridad
from app.models.centro_educativo import CentroEducativo
from app.models.dato_catastral import DatoCatastral
from app.models.escenario_deportivo import EscenarioDeportivo
from app.models.estacion_transporte import EstacionTransporte
from app.models.estado_calle import EstadoCalle
from app.models.faq_item import FaqItem
from app.models.foto import Foto
from app.models.historia_hito import HistoriaHito
from app.models.libreria import Libreria
from app.models.localidad_kennedy import LocalidadKennedy
from app.models.robo import Robo
from app.models.sitio_comida import SitioComida
from app.models.usuario import Usuario
from app.models.veterinaria import Veterinaria
from app.models.zona_verde import ZonaVerde

__all__ = [
    "AtencionInmediata", "Barberia", "Calificacion", "CamaraSeguridad", "CentroEducativo",
    "DatoCatastral", "EscenarioDeportivo", "EstacionTransporte", "EstadoCalle", "FaqItem",
    "Foto", "HistoriaHito", "Libreria", "LocalidadKennedy", "Robo", "SitioComida",
    "Usuario", "Veterinaria", "ZonaVerde",
]
