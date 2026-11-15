"""Carga seed/fotos.json: fotos reales de Wikimedia Commons de lugares del barrio (D66).

Uso (desde barrio-backend/): python -m etl.runner --solo fotos
- Cada foto apunta a su lugar por el source_ref del registro (OpenStreetMap),
  que es igual en desarrollo y en producción; los id no lo son.
- Es idempotente: borra las fotos con el mismo source_ref y las vuelve a crear.
- Una foto cuyo lugar no existe no se carga y se informa en "sin_lugar".
- Se rechaza el archivo entero si una foto no cumple la regla de rutas locales
  o le falta autor, licencia o la página de Commons.
"""

import json
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, delete, select
from sqlalchemy.orm import Session

from app.models import Foto
from app.modules.registry import MODULES
from app.schemas.engagement import FotoIn

SEED = Path(__file__).resolve().parent.parent / "seed" / "fotos.json"
COMMONS = "https://commons.wikimedia.org/wiki/File:"
SPECS = {spec.slug: spec for spec in MODULES}


def read(path: Path = SEED) -> list[dict[str, Any]]:
    fotos: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))["fotos"]
    for foto in fotos:
        FotoIn.model_validate({k: foto[k] for k in ("url", "alt_text", "orden", "autor", "licencia")})
        if foto["modulo"] not in SPECS:
            raise ValueError(f"módulo desconocido: {foto['modulo']}")
        if not (foto["autor"] and foto["licencia"] and foto["source_ref"].startswith(COMMONS)):
            raise ValueError(f"{foto['url']}: falta autor, licencia o la página de Commons")
    return fotos


def _place_id(session: Session, foto: dict[str, Any]) -> int | None:
    model: Any = SPECS[foto["modulo"]].model
    return session.scalar(select(model.id).where(model.source_ref == foto["lugar_ref"]))


def run(engine: Engine, path: Path = SEED) -> dict[str, Any]:
    fotos = read(path)
    missing: list[str] = []
    with Session(engine) as session:
        session.execute(delete(Foto).where(Foto.source_ref.in_([f["source_ref"] for f in fotos])))
        for foto in fotos:
            place = _place_id(session, foto)
            if place is None:
                missing.append(foto["url"])
                continue
            session.add(Foto(categoria_slug=foto["modulo"], objeto_id=place, url=foto["url"],
                             alt_text=foto["alt_text"], orden=foto["orden"], autor=foto["autor"],
                             licencia=foto["licencia"], source_type="seed",
                             source_ref=foto["source_ref"], verified=True))
        session.commit()
    return {"loaded": len(fotos) - len(missing), "sin_lugar": missing}
