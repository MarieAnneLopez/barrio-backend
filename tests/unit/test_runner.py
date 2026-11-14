"""Orquestador del ETL: orden de pasos, --solo, --con-base y errores claros."""

import pytest

from etl.runner import main

ORDER = ["base", "osm", "datos-abiertos", "ejemplos", "carga"]


def _fake(log: list[str]) -> dict:
    return {name: (lambda engine, n=name: log.append(n) or n) for name in ORDER}


def test_por_defecto_todo_menos_la_base() -> None:
    log: list[str] = []
    assert list(main([], engine=object(), available=_fake(log))) == ORDER[1:]
    assert log == ORDER[1:]


def test_con_base_y_solo_respetan_el_orden() -> None:
    log: list[str] = []
    main(["--con-base"], engine=object(), available=_fake(log))
    assert log == ORDER
    log.clear()
    main(["--solo", "carga,osm"], engine=object(), available=_fake(log))
    assert log == ["osm", "carga"]


def test_paso_desconocido_falla_sin_ejecutar_nada() -> None:
    log: list[str] = []
    with pytest.raises(SystemExit):
        main(["--solo", "osm,nada"], engine=object(), available=_fake(log))
    assert log == []
