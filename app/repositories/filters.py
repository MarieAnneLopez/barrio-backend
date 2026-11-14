"""Búsqueda, filtros y orden seguros: solo columnas permitidas y valores tipados.

Todo pasa por expresiones de SQLAlchemy (consultas parametrizadas); el texto
del usuario nunca se concatena en SQL.
"""

from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

from sqlalchemy import Boolean, Date, Integer, Numeric, Select, or_
from sqlalchemy.orm import InstrumentedAttribute

from app.core.exceptions import AppError


def invalid(field: str, message: str) -> AppError:
    return AppError("VALIDATION_ERROR", message, 422, [{"loc": ["query", field], "msg": message}])


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _coerce(column: InstrumentedAttribute[Any], name: str, raw: str) -> Any:
    kind = column.type
    try:
        if isinstance(kind, Boolean):
            if raw.lower() not in ("true", "false"):
                raise ValueError(raw)
            return raw.lower() == "true"
        if isinstance(kind, Integer):
            return int(raw)
        if isinstance(kind, Numeric):
            return float(raw)
        if isinstance(kind, Date):
            return date.fromisoformat(raw)
    except ValueError as exc:
        raise invalid(name, f"Valor inválido para el filtro {name}") from exc
    return raw


def apply_search(stmt: Select[Any], columns: Sequence[InstrumentedAttribute[Any]], q: str) -> Select[Any]:
    pattern = f"%{_escape_like(q.strip())}%"
    return stmt.where(or_(*(col.ilike(pattern, escape="\\") for col in columns)))


def apply_filters(
    stmt: Select[Any], model: type, allowed: Sequence[str], filters: Mapping[str, str]
) -> Select[Any]:
    for name, raw in filters.items():
        if name not in allowed:
            raise invalid(name, f"Filtro no permitido: {name}")
        column = getattr(model, name)
        stmt = stmt.where(column == _coerce(column, name, raw))
    return stmt


def apply_sort(stmt: Select[Any], model: type, allowed: Sequence[str], sort: str | None) -> Select[Any]:
    if not sort:
        return stmt.order_by(model.id)  # type: ignore[attr-defined]
    name = sort.removeprefix("-")
    if name not in allowed:
        raise invalid("sort", f"Orden no permitido en sort: {name}")
    column = getattr(model, name)
    return stmt.order_by(column.desc() if sort.startswith("-") else column.asc(), model.id)  # type: ignore[attr-defined]
