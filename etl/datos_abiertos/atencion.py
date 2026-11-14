"""Datos abiertos → Módulo 12 · Centros de Atención Inmediata.

CAI: capa oficial de la SDSCJ (horario y teléfono de la propia fuente).
Hospitales: IPS públicas de la SDS cuyo nombre las identifica como Unidad de
Servicios de Salud u hospital. Las demás IPS (ópticas, odontología, estética)
no son atención inmediata y se omiten con motivo.
"""

from typing import Any

from etl.datos_abiertos.sources import CAI, IPS

HOSPITAL_WORDS = ("unidad de servicios de salud", "hospital")


def _point(feature: dict[str, Any]) -> dict[str, Any]:
    lon, lat = feature["geometry"]["coordinates"][:2]
    return {"type": "Point", "coordinates": [round(lon, 7), round(lat, 7)]}


def cai_features(data: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for f in data["features"]:
        p = f["properties"]
        always = "24 horas" in (p.get("CAIHORARIO") or "")
        props = {
            "nombre": p["CAINOMBRE"].strip(), "tipo": "cai",
            "direccion": (p.get("CAIDIR_SIT") or "").strip() or None,
            "telefono_24_7": str(p["CAITELEFON"]).strip() if always and p.get("CAITELEFON") else None,
            "source_type": "datos_abiertos",
            "source_ref": f"{CAI.page}#{p['CAIIDENTIF']}", "verified": True,
        }
        out.append({"type": "Feature", "properties": props, "geometry": _point(f)})
    return out


def ips_features(data: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """(hospitales, omitidas con motivo)."""
    keep, skipped = [], []
    for f in data["features"]:
        if not f.get("geometry"):
            continue
        p = f["properties"]
        name = " ".join((p.get("nombre") or "").split())
        is_hospital = any(w in name.lower() for w in HOSPITAL_WORDS)
        ref = f"{IPS.page}#{p.get('codigo_pre')}"
        if not is_hospital:
            skipped.append({"ref": ref, "name": name, "reason": "IPS sin atención inmediata declarada"})
            continue
        props = {"nombre": name[:200], "tipo": "hospital",
                 "direccion": (p.get("direccion") or "").strip()[:200] or None,
                 "telefono_24_7": None, "source_type": "datos_abiertos",
                 "source_ref": ref, "verified": True}
        keep.append({"type": "Feature", "properties": props, "geometry": _point(f)})
    return keep, skipped
