"""Carga seed/fotos.json (Wikimedia Commons, D66) y seed/fotos_mapillary.json (Mapillary, H35).

Uso (desde barrio-backend/): python -m etl.runner --solo fotos
- Cada foto apunta a su lugar por el source_ref del registro (OpenStreetMap),
  que es igual en desarrollo y en producción; los id no lo son.
- Es idempotente: borra las fotos con el mismo source_ref y las vuelve a crear.
- Una foto cuyo lugar no existe no se carga y se informa en "sin_lugar".
- Se rechaza el archivo entero si una foto no cumple la regla de rutas locales
  o le falta autor, licencia o la página de origen (Commons o Mapillary).
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
SEED_MAPILLARY = SEED.with_name("fotos_mapillary.json")
COMMONS = "https://commons.wikimedia.org/wiki/File:"
MAPILLARY = "https://www.mapillary.com/app/?pKey="
SPECS = {spec.slug: spec for spec in MODULES}


def read(path: Path = SEED) -> list[dict[str, Any]]:
    fotos: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))["fotos"]
    for foto in fotos:
        FotoIn.model_validate({k: foto.get(k) for k in ("url", "alt_text", "alt_text_en", "orden", "autor", "licencia")})
        if foto["modulo"] not in SPECS:
            raise ValueError(f"módulo desconocido: {foto['modulo']}")
        if not (foto["autor"] and foto["licencia"] and foto["source_ref"].startswith((COMMONS, MAPILLARY))):
            raise ValueError(f"{foto['url']}: falta autor, licencia o la página de Commons o Mapillary")
    return fotos


def _place_id(session: Session, foto: dict[str, Any]) -> int | None:
    model: Any = SPECS[foto["modulo"]].model
    return session.scalar(select(model.id).where(model.source_ref == foto["lugar_ref"]))


def run(engine: Engine, path: Path | None = None) -> dict[str, Any]:
    paths = [path] if path else [p for p in (SEED, SEED_MAPILLARY) if p.exists()]
    fotos = [foto for p in paths for foto in read(p)]
    missing: list[str] = []
    with Session(engine) as session:
        session.execute(delete(Foto).where(Foto.source_ref.in_([f["source_ref"] for f in fotos])))
        for foto in fotos:
            place = _place_id(session, foto)
            if place is None:
                missing.append(foto["url"])
                continue
            session.add(Foto(categoria_slug=foto["modulo"], objeto_id=place, url=foto["url"],
                             alt_text=foto["alt_text"], alt_text_en=foto.get("alt_text_en"),
                             orden=foto["orden"], autor=foto["autor"],
                             licencia=foto["licencia"], source_type="seed",
                             source_ref=foto["source_ref"], verified=True))
        session.commit()
    return {"loaded": len(fotos) - len(missing), "sin_lugar": missing}
