"""Carga seed/historia.json en historia_hitos; reemplaza todos los hitos de la semilla.

Uso (desde barrio-backend/): python -m etl.runner --solo historia
Cada hito debe citar una fuente del catálogo del mismo archivo (D55); si no,
se rechaza todo el archivo para no publicar hitos sin trazabilidad. Un hito
quitado de la semilla (D56) también sale de la base al recargar.
"""

import json
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, delete
from sqlalchemy.orm import Session

from app.models.historia_hito import HistoriaHito

SEED = Path(__file__).resolve().parent.parent / "seed" / "historia.json"
FIELDS = ("anio", "orden", "titulo", "descripcion", "source_ref", "verified")


def read(path: Path = SEED) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    known = {f["url"] for f in data["fuentes"] if f.get("url")}
    hitos = [{k: h[k] for k in FIELDS} for h in data["hitos"]]
    for hito in hitos:
        refs = set(hito["source_ref"].split(" | "))
        if not refs <= known:
            raise ValueError(f"{hito['anio']} cita fuentes fuera del catálogo: {refs - known}")
    return hitos


def run(engine: Engine, path: Path = SEED) -> dict[str, int]:
    hitos = read(path)
    with Session(engine) as session:
        session.execute(delete(HistoriaHito).where(HistoriaHito.source_type == "seed"))
        session.add_all(HistoriaHito(source_type="seed", **h) for h in hitos)
        session.commit()
    return {"loaded": len(hitos), "verified": sum(h["verified"] for h in hitos)}
