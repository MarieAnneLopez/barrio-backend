"""Formato único de error: {"error": {"code", "message", "details"}}.

Nunca se exponen trazas ni detalles internos; esos van al log del servidor.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

HTTP_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "TOO_MANY_ATTEMPTS",
    503: "SERVICE_UNAVAILABLE",
}


class AppError(Exception):
    """Error de dominio con código estable y estado HTTP."""

    def __init__(self, code: str, message: str, status_code: int = 400, details: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


class DatabaseUnavailableError(AppError):
    def __init__(self) -> None:
        super().__init__("DATABASE_UNAVAILABLE", "La base de datos no responde", 503)


class ConflictError(AppError):
    def __init__(self, table: str) -> None:
        super().__init__("CONFLICT", f"El registro choca con otro de {table} (p. ej. código repetido)", 409)


def error_body(code: str, message: str, details: Any = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return {"error": error}


async def _app_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    return JSONResponse(error_body(exc.code, exc.message, exc.details), exc.status_code)


async def _http_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    code = HTTP_CODES.get(exc.status_code, "HTTP_ERROR")
    return JSONResponse(error_body(code, str(exc.detail)), exc.status_code, headers=exc.headers)


async def _validation_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    details = [
        {"loc": list(err.get("loc", [])), "msg": err.get("msg"), "type": err.get("type")}
        for err in exc.errors()
    ]
    return JSONResponse(error_body("VALIDATION_ERROR", "Datos inválidos", details), 422)


async def _database_down(_: Request, exc: Exception) -> JSONResponse:
    logger.warning("Base de datos no disponible: %s", type(exc).__name__)
    return JSONResponse(error_body("DATABASE_UNAVAILABLE", "La base de datos no responde"), 503)


async def _unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    return JSONResponse(error_body("INTERNAL_ERROR", "Error interno del servidor"), 500)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(OperationalError, _database_down)
    app.add_exception_handler(Exception, _unhandled_error)
