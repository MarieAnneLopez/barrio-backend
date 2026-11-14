"""Robos, atención, localidad y GeoPackage: parseo fiel de las fuentes oficiales."""

import struct

import pytest

from etl.datos_abiertos import atencion, localidad, robos
from etl.datos_abiertos.gpkg import wkb

HEADER = '"ID";"ANIO";"MES";"TIPO_INCIDENTE";"TIPO_DETALLE";"COD_LOCALIDAD";"LOCALIDAD";' \
         '"COD_UPZ";"UPZ";"CANT_INCIDENTES"\n'
POINTS = {"UPZ78": [-74.16, 4.65], "UPZ79": [-74.15, 4.65]}


def _row(id_: str, year: str, month: str, kind: str, upz: str, n: int) -> str:
    return f'"{id_}";"{year}";"{month}";"904";"{kind}";"08";"KENNEDY";"{upz}";"X";{n}\n'


def test_robos_filtra_upz_modalidad_y_ventana() -> None:
    text = HEADER + _row("A", "2024", "03", "HURTO EFECTUADO", "UPZ79", 26) \
        + _row("B", "2023", "12", "HURTO EFECTUADO", "UPZ79", 9) \
        + _row("C", "2024", "03", "RIÑA", "UPZ79", 4) + _row("D", "2025", "01", "HURTO EN PROCESO", "UPZ80", 3)

    [feature] = robos.features(text, POINTS)
    p = feature["properties"]

    assert (p["fecha"], p["modalidad"], p["cantidad"], p["franja_horaria"]) == \
        ("2024-03-01", "Hurto efectuado", 26, None)
    assert "no denuncias" in p["fuente"] and p["source_ref"].endswith("#A")
    assert feature["geometry"]["coordinates"] == POINTS["UPZ79"]


def test_cai_solo_publica_el_telefono_si_atiende_24_horas() -> None:
    def cai(name: str, horario: str) -> dict:
        return {"properties": {"CAINOMBRE": f" {name} ", "CAIDIR_SIT": "CL 6D KR 87A", "CAITELEFON": 313,
                               "CAIHORARIO": horario, "CAIIDENTIF": name},
                "geometry": {"type": "Point", "coordinates": [-74.1512345678, 4.65, 0]}}

    a, b = atencion.cai_features({"features": [cai("CAI Tintal", "24 horas - lunes a domingo"),
                                                cai("CAI Otro", "diurno")]})

    assert a["properties"]["nombre"] == "CAI Tintal" and a["properties"]["telefono_24_7"] == "313"
    assert b["properties"]["telefono_24_7"] is None
    assert a["geometry"]["coordinates"] == [-74.1512346, 4.65]


def test_ips_solo_hospitales_y_omite_el_resto_con_motivo() -> None:
    def ips(name: str) -> dict:
        return {"properties": {"nombre": name, "codigo_pre": name[:3], "direccion": "CALLE 10"},
                "geometry": {"type": "Point", "coordinates": [-74.15, 4.65]}}

    keep, skipped = atencion.ips_features({"features": [
        ips("Unidad de Servicios de Salud  Patio Bonito"), ips("ÓPTICA SOL"), {"geometry": None}]})

    assert [f["properties"]["nombre"] for f in keep] == ["Unidad de Servicios de Salud Patio Bonito"]
    assert skipped[0]["reason"] == "IPS sin atención inmediata declarada"


def test_poblacion_suma_kennedy_del_anio_y_alcaldia() -> None:
    csv = "ANO;CODIGO_LOCALIDAD;NOMBRE_LOCALIDAD;POBLACION\n2026;8;Kennedy;10\n2026;8;Kennedy;5\n" \
          "2025;8;Kennedy;99\n2026;9;Fontibón;7\n"
    layer = {"features": [{"attributes": {"COD_LOC": "08", "NOM_ALCALDIA": "Alcaldía Local de Kennedy ",
                                          "DIRECCION": " Calle 19 Sur # 69C -17"}}]}

    assert localidad.population(csv) == 15
    assert localidad.alcaldia(layer) == "Alcaldía Local de Kennedy, Calle 19 Sur # 69C -17"
    with pytest.raises(ValueError):
        localidad.alcaldia({"features": []})


@pytest.mark.parametrize(("envelope", "size"), [(0, 0), (1, 32), (2, 48), (4, 64)])
def test_wkb_quita_el_encabezado_gpkg(envelope: int, size: int) -> None:
    body = b"\x01\x01\x00\x00\x00" + struct.pack("<dd", -74.15, 4.65)
    blob = b"GP\x00" + bytes([envelope << 1 | 1]) + struct.pack("<i", 4326) + b"\x00" * size + body

    assert wkb(blob) == body
    with pytest.raises(ValueError):
        wkb(b"XX" + blob[2:])
