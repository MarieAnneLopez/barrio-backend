"""Cabeceras de seguridad en cada respuesta de la API (OWASP)."""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

# La API solo sirve JSON: CSP cerrada. La documentación interactiva (/docs)
# carga sus scripts propios, así que queda fuera de esa CSP.
DOC_PATHS = ("/docs", "/redoc", "/openapi.json")
BASE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}
API_CSP = "default-src 'none'; frame-ancestors 'none'"


def register_security_headers(app: FastAPI) -> None:
    @app.middleware("http")
    async def add_security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        for name, value in BASE_HEADERS.items():
            response.headers.setdefault(name, value)
        if not request.url.path.startswith(DOC_PATHS):
            response.headers.setdefault("Content-Security-Policy", API_CSP)
        return response
