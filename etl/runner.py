"""Orquestador del ETL completo de El Tintal (H15).

Uso (desde barrio-backend/, con PostGIS arriba):
    python -m etl.runner                 # módulos OSM + datos abiertos + ejemplos + carga
    python -m etl.runner --con-base      # además rehace polígono y capas base (H7)
    python -m etl.runner --solo osm,carga
Cada paso es idempotente: se puede repetir sin duplicar registros.
"""

import argparse
from collections.abc import Callable
from typing import Any

from sqlalchemy import Engine

from app.core.database import get_engine
from etl import examples, import_datos_abiertos, import_modules, import_osm, load_seed
from etl.datos_abiertos.client import OpenDataClient
from etl.overpass import OverpassClient

Step = Callable[[Engine], Any]


def _in_tx(fn: Callable[..., Any], *args: Any) -> Step:
    def step(engine: Engine) -> Any:
        with engine.begin() as conn:
            return fn(conn, *args)
    return step


def steps(osm: OverpassClient, data: OpenDataClient) -> dict[str, Step]:
    return {
        "base": lambda engine: import_osm.run(osm, engine)["layers"],
        "osm": _in_tx(lambda conn: import_modules.run(osm, conn)),
        "datos-abiertos": _in_tx(lambda conn: import_datos_abiertos.run(conn, osm, data)),
        "ejemplos": _in_tx(examples.run),
        "carga": load_seed.run,
    }


def main(argv: list[str] | None = None, engine: Engine | None = None,
         available: dict[str, Step] | None = None) -> dict[str, Any]:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--con-base", action="store_true")
    parser.add_argument("--solo", help="pasos separados por coma: base,osm,datos-abiertos,ejemplos,carga")
    args = parser.parse_args(argv)
    available = available or steps(OverpassClient(), OpenDataClient())
    order = list(available) if args.con_base else [s for s in available if s != "base"]
    if args.solo:
        wanted = args.solo.split(",")
        unknown = set(wanted) - set(available)
        if unknown:
            parser.error(f"pasos desconocidos: {', '.join(sorted(unknown))}")
        order = [s for s in available if s in wanted]
    engine = engine or get_engine()
    results = {}
    for name in order:
        results[name] = available[name](engine)
        print(f"[{name}] {results[name]}")
    return results


if __name__ == "__main__":
    main()
