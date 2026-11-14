"""Estado de la API y de su base geoespacial."""

from app.core.exceptions import DatabaseUnavailableError
from app.repositories.interfaces import DatabaseProbe
from app.schemas.health import HealthReport


class HealthService:
    """Depende de la abstracción DatabaseProbe, no de SQLAlchemy (DIP)."""

    def __init__(self, probe: DatabaseProbe) -> None:
        self._probe = probe

    def check(self) -> HealthReport:
        try:
            version = self._probe.postgis_version()
        except DatabaseUnavailableError:
            return HealthReport(status="degraded", database="unavailable", postgis=None)
        return HealthReport(status="ok", database="ok", postgis=version)
