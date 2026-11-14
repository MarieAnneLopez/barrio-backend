"""Contratos pequeños y específicos (ISP) de los que dependen los servicios (DIP).

Las implementaciones concretas viven en este mismo paquete; los servicios
solo conocen estos protocolos.
"""

from typing import Any, Protocol


class DatabaseProbe(Protocol):
    """Comprueba que la base responde y tiene PostGIS."""

    def postgis_version(self) -> str:
        """Versión de PostGIS; lanza DatabaseUnavailableError si la base no responde."""
        ...


class BarrioRepository(Protocol):
    """Fuente del polígono oficial de El Tintal (GeoJSON Feature, SRID 4326)."""

    def polygon_feature(self) -> dict[str, Any]:
        """Feature con geometry, bbox y properties de trazabilidad."""
        ...
