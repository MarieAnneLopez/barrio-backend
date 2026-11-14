from app.services.health_service import HealthService
from tests.conftest import FakeProbe


def test_reporta_ok_con_la_version_de_postgis() -> None:
    report = HealthService(FakeProbe("3.4 USE_GEOS=1")).check()

    assert report.status == "ok"
    assert report.database == "ok"
    assert report.postgis == "3.4 USE_GEOS=1"


def test_reporta_degradado_si_la_base_no_responde() -> None:
    report = HealthService(FakeProbe(version=None)).check()

    assert report.status == "degraded"
    assert report.database == "unavailable"
    assert report.postgis is None
