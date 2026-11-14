"""Datos abiertos → Módulo 10 · Datos sobre Robos (agregados y anonimizados).

Fuente: llamadas a la Línea 123 (NUSE) tipificadas como hurto, por UPZ y mes.
Son reportes ciudadanos, no denuncias ni hechos confirmados: así lo dice el
campo `fuente`. Cada registro agrega un mes, una UPZ y una modalidad; se ubica
en un punto interior de la UPZ (ST_PointOnSurface), nunca en una dirección.
La fuente no trae la hora: franja_horaria queda nula (D51).
"""

import csv
import io
from datetime import date
from typing import Any

from etl.datos_abiertos.sources import NUSE_123

UPZ = {"UPZ78": "UPZ 78 Tintal Norte", "UPZ79": "UPZ 79 Calandaima"}
MODALIDADES = {"HURTO EFECTUADO": "Hurto efectuado",
               "ATRACO / HURTO EN PROCESO": "Atraco / hurto en proceso",
               "HURTO EN PROCESO": "Hurto en proceso"}
DESDE = (2024, 1)  # ventana: de enero de 2024 al último mes publicado


def features(csv_text: str, points: dict[str, list[float]]) -> list[dict[str, Any]]:
    """Un Feature por (UPZ, mes, modalidad) con su cantidad de llamadas."""
    out = []
    for row in csv.DictReader(io.StringIO(csv_text), delimiter=";"):
        upz, kind = row["COD_UPZ"], row["TIPO_DETALLE"].strip()
        year, month = int(row["ANIO"]), int(row["MES"])
        if upz not in UPZ or kind not in MODALIDADES or (year, month) < DESDE:
            continue
        props = {
            "fecha": date(year, month, 1).isoformat(),
            "franja_horaria": None,
            "modalidad": MODALIDADES[kind],
            "fuente": f"Línea 123 (NUSE), SDSCJ: llamadas tipificadas, {UPZ[upz]}, "
                      f"{year}-{month:02d}. Reportes, no denuncias.",
            "cantidad": int(row["CANT_INCIDENTES"]),
            "source_type": "datos_abiertos",
            "source_ref": f"{NUSE_123.page}#{row['ID']}",
            "verified": True,
        }
        out.append({"type": "Feature", "properties": props,
                    "geometry": {"type": "Point", "coordinates": points[upz]}})
    return out
