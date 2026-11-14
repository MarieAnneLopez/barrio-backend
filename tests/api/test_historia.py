"""GET /api/v1/historia y su carga: orden, trazabilidad, fuentes y D55."""

import json
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.historia import get_historia_service
from app.core.database import get_engine
from app.models.historia_hito import HistoriaHito
from app.repositories.historia_repository import SqlHistoriaRepository
from app.services.historia_service import HistoriaService
from etl import load_historia
from tests.conftest import make_client

OFICIAL_KENNEDY = "https://bogota.gov.co/mi-ciudad/localidades/kennedy/historia-del-poblamiento-de-kennedy"


async def test_linea_de_tiempo_ordenada_con_fuentes(client: AsyncClient, db_session: Session) -> None:
    load_historia.run(get_engine())

    body = (await client.get("/api/v1/historia")).json()

    years = [h["anio"] for h in body["hitos"]]
    assert years == sorted(years)
    by_year = {h["anio"]: h for h in body["hitos"]}
    assert by_year[1963]["verified"] and by_year[1963]["source_ref"] == OFICIAL_KENNEDY
    assert by_year[1967]["titulo"] == "El Concejo ratifica el nombre"
    assert "junio de 2001" in by_year[2001]["descripcion"]
    assert not by_year[1992]["verified"]
    assert body["consultado"] == "2026-11-14"
    tipos = [f["tipo"] for f in body["fuentes"]]
    assert tipos[:2] == ["oficial", "oficial"] and tipos[-1] == "comunitaria"


def test_d55_sin_las_fechas_descartadas() -> None:
    text = json.dumps(load_historia.read(), ensure_ascii=False)
    assert "hasta 1963" not in text and "hasta 1964" not in text
    assert all(h["anio"] != 2002 for h in load_historia.read())


def test_la_carga_es_idempotente(db_session: Session) -> None:
    first = load_historia.run(get_engine())
    load_historia.run(get_engine())

    count = db_session.scalar(select(func.count()).select_from(HistoriaHito))
    assert count == first["loaded"] and first["verified"] == 6


def test_rechaza_hitos_sin_fuente_del_catalogo(tmp_path: Path) -> None:
    data = json.loads(load_historia.SEED.read_text(encoding="utf-8"))
    data["hitos"][0]["source_ref"] = "https://ejemplo.invalido/historia"
    seed = tmp_path / "historia.json"
    seed.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="fuera del catálogo"):
        load_historia.read(seed)


async def test_sin_catalogo_responde_503(app, db_session: Session, tmp_path: Path) -> None:
    missing = SqlHistoriaRepository(db_session, tmp_path / "no.json")
    app.dependency_overrides[get_historia_service] = lambda: HistoriaService(missing)
    async with make_client(app) as http:
        response = await http.get("/api/v1/historia")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SEED_UNAVAILABLE"
